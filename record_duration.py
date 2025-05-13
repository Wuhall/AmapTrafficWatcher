import requests
import json
import time
from datetime import datetime
import matplotlib.pyplot as plt
import os
from typing import Optional, Dict, List
import logging
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.getenv("LOG_FILE", "traffic_monitor.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TrafficMonitor:
    def __init__(self):
        # 从环境变量读取配置
        self.api_url = os.getenv("AMAP_API_BASE_URL", "https://restapi.amap.com/v3") + "/direction/driving"
        self.params = {
            "origin": os.getenv("DEFAULT_ORIGIN"),
            "destination": os.getenv("DEFAULT_DESTINATION"),
            "extensions": "base",
            "strategy": "10",
            "output": "json",
            "key": os.getenv("AMAP_API_KEY"),
        }
        
        # 验证必要的环境变量
        self._validate_env_vars()
        
        self.data_file = Path("data/hourly_durations.json")
        self.visualization_folder = Path("visualizations")
        self.latest_image = self.visualization_folder / "latest.png"
        
        # 初始化目录和文件
        self._initialize_storage()
        
    def _validate_env_vars(self):
        """验证必要的环境变量是否存在"""
        required_vars = ["AMAP_API_KEY", "DEFAULT_ORIGIN", "DEFAULT_DESTINATION"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
    def _initialize_storage(self):
        """初始化存储目录和文件"""
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.visualization_folder.mkdir(exist_ok=True)
        
        if not self.data_file.exists():
            with open(self.data_file, "w") as f:
                json.dump([], f)
    
    def fetch_duration(self) -> Optional[float]:
        """获取行程时间"""
        try:
            response = requests.get(self.api_url, params=self.params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "1" and "route" in data and "paths" in data["route"]:
                duration_seconds = int(data["route"]["paths"][0]["duration"])
                return duration_seconds / 3600  # 转换为小时
            else:
                logger.error(f"Unexpected API response: {data}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None

    def record_duration(self, duration: float) -> None:
        """记录行程时间"""
        timestamp = datetime.now()
        record = {
            "timestamp": timestamp.isoformat(),
            "date": timestamp.strftime("%Y-%m-%d"),
            "time": timestamp.strftime("%H:%M:%S"),
            "duration": round(duration, 2),
        }

        try:
            with open(self.data_file, "r") as f:
                data = json.load(f)

            data.append(record)

            with open(self.data_file, "w") as f:
                json.dump(data, f, indent=4)
                
            logger.info(f"Recorded duration: {duration:.2f} hours")
        except Exception as e:
            logger.error(f"Error recording duration: {e}")

    def visualize_data(self) -> None:
        """可视化数据"""
        try:
            with open(self.data_file, "r") as f:
                data = json.load(f)

            if not data:
                logger.warning("No data to visualize")
                return

            # 准备数据
            dates = [item["date"] for item in data]
            times = [item["time"] for item in data]
            durations = [item["duration"] for item in data]

            # 创建图表
            plt.figure(figsize=(12, 6))
            plt.plot(range(len(durations)), durations, marker="o", linestyle="-", linewidth=1)
            
            # 设置x轴标签
            plt.xticks(range(len(durations)), [f"{d}\n{t}" for d, t in zip(dates, times)], 
                      rotation=45, fontsize=8)
            
            plt.xlabel("Date and Time")
            plt.ylabel("Duration (hours)")
            plt.title("Traffic Duration Over Time")
            plt.grid(True, linestyle="--", alpha=0.7)
            plt.tight_layout()

            # 保存图像
            timestamp = datetime.now().strftime("%Y%m%d%H")
            output_path = self.visualization_folder / f"traffic_duration_{timestamp}.png"
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            plt.savefig(self.latest_image, dpi=300, bbox_inches="tight")
            plt.close()
            
            logger.info(f"Visualization saved: {output_path}")
        except Exception as e:
            logger.error(f"Error creating visualization: {e}")

    def run(self):
        """运行监控"""
        logger.info("Starting traffic monitor...")
        while True:
            now = datetime.now()
            if now.second == 0:  # 每分钟运行
            # if now.minute == 0 and now.second == 0:  # 每小时整点运行
                logger.info(f"Fetching data at {now.strftime('%Y-%m-%d %H:%M:%S')}...")
                duration = self.fetch_duration()
                if duration is not None:
                    self.record_duration(duration)
                    self.visualize_data()
                time.sleep(1)  # 防止重复触发
            time.sleep(1)

def main():
    try:
        monitor = TrafficMonitor()
        monitor.run()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
    except KeyboardInterrupt:
        logger.info("Traffic monitor stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}")

if __name__ == "__main__":
    main()

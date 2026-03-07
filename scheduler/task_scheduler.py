import subprocess
import schedule
import time
import yaml
import logging
from pathlib import Path
import concurrent.futures

executor = concurrent.futures.ThreadPoolExecutor()

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

scheduled_jobs = {}  # name -> job

def load_config(path="tasks.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def log_setup(task_name):
    log_file = LOG_DIR / f"{task_name}.log"
    logger = logging.getLogger(task_name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

def run_task(task, all_tasks_by_name):
    def task_runner():
        name = task["name"]
        task_type = task["type"]
        path = task["path"]
        args = task.get("args", [])
        logger = log_setup(name)

        logger.info(f"Запуск задачи '{name}' ({task_type})")

        try:
            if task_type == "script":
                result = subprocess.run(["python", path] + args, capture_output=True, text=True)
            elif task_type == "pytest":
                result = subprocess.run(["pytest", path] + args, capture_output=True, text=True)
            else:
                logger.error(f"Неизвестный тип задачи: {task_type}")
                return

            logger.info("stdout:\n" + result.stdout)
            logger.info("stderr:\n" + result.stderr)

            if result.returncode == 0:
                logger.info("Задача завершена успешно.")
                for next_name in task.get("on_success", []):
                    next_task = all_tasks_by_name.get(next_name)
                    if next_task:
                        logger.info(f"Запуск зависимости (успех) '{next_name}'")
                        executor.submit(run_task, next_task, all_tasks_by_name)
            else:
                logger.error(f"Задача завершилась с ошибкой. Код: {result.returncode}")
                for next_name in task.get("on_error", []):
                    next_task = all_tasks_by_name.get(next_name)
                    if next_task:
                        logger.info(f"Запуск зависимости (ошибка) '{next_name}'")
                        executor.submit(run_task, next_task, all_tasks_by_name)

                if name in scheduled_jobs:
                    logger.warning(f"Остановка задачи '{name}' из расписания из-за ошибки")
                    schedule.cancel_job(scheduled_jobs[name])
                    del scheduled_jobs[name]

        except Exception as e:
            logger.exception(f"Ошибка при запуске задачи '{name}': {e}")

    # Запускаем задачу асинхронно
    executor.submit(task_runner)

def schedule_task(task, all_tasks_by_name):
    sched = task.get("schedule")
    if not sched:
        return  # не по расписанию, вызывается только вручную

    def job():
        run_task(task, all_tasks_by_name)

    if sched.startswith("every"):
        parts = sched.split()
        interval = int(parts[1])
        unit = parts[2]

        if unit.startswith("minute"):
            job_ref = schedule.every(interval).minutes.do(job)
        elif unit.startswith("hour"):
            job_ref = schedule.every(interval).hours.do(job)
        else:
            raise ValueError(f"Неподдерживаемый интервал: {unit}")

        scheduled_jobs[task["name"]] = job_ref
    else:
        raise ValueError(f"Неверный формат расписания: {sched}")

def main():
    config = load_config()
    all_tasks = config.get("tasks", [])
    all_tasks_by_name = {task["name"]: task for task in all_tasks}

    for task in all_tasks:
        try:
            schedule_task(task, all_tasks_by_name)
            if "schedule" in task:
                print(f"Задача '{task['name']}' добавлена в расписание.")
        except Exception as e:
            print(f"Ошибка при добавлении задачи '{task['name']}': {e}")

    print("Планировщик запущен. Нажмите Ctrl+C для выхода.")
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()

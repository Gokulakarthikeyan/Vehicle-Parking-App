from app import celery  # your Celery instance

if __name__ == "__main__":
    # Start Celery worker programmatically
    celery.worker_main(argv=['worker','--loglevel=info','--pool=solo'])

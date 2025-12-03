# main.py
"""
程序入口
"""
if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    multiprocessing.set_start_method("spawn", force=True)

    from ui import run_app
    run_app()
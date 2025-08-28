import os
import uvicorn

def main():
    """Главная функция для запуска приложения"""
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("apps.api.app_factory:create_app", host="0.0.0.0", port=port, reload=True)

if __name__ == "__main__":
    main()

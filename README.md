# 🎯 TrendHunter AI

<div align="center">

**AI-мониторинг инфоповодов и генерация идей под GEO**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-red.svg)](LICENSE)

</div>

## 📋 О проекте

**TrendHunter AI** — это интеллектуальная система для автоматического мониторинга инфоповодов и генерации маркетинговых идей под конкретные географические регионы (GEO).

### 🎯 Проблема, которую решает

- Копирайтеры тратят **1-3 часа** на ручной поиск инфоповодов
- Сложно находить свежие локальные темы для разных стран
- Высокий риск выгорания при регулярном поиске идей
- Отсутствие системного подхода к мониторингу

### ✨ Решение

- ⚡ **Экономия времени**: от 1-3 часов → 15 минут на проверку
- 🌍 **Локализация**: автоматический учёт культурных особенностей
- 💡 **Постоянный поток идей**: 30-50 готовых заголовков за запуск
- 🎯 **Таргетирование**: привязка к офферу и эмоциональным триггерам

## 🚀 Быстрый старт

### Требования

- Python 3.11 или выше
- Опционально: Docker и Docker Compose
- Опционально: Ollama (для локальной работы)

### Как работать с LLM (Ollama)
```bash
- Установите Ollama (для локальной работы)
# Скачайте Ollama для Windows:
# https://ollama.com/download/windows

# После установки, запустите в PowerShell:
ollama pull mistral

# Или более легкую модель:
ollama pull tinyllama

# Запустите сервер:
ollama serve
```


### Установка

```bash
# Клонирование репозитория
git clone https://github.com/your-username/trendhunter-ai.git
cd trendhunter-ai

# Создание виртуального окружения
python -m venv venv

# Активация (Windows)
venv\Scripts\activate
# Активация (Linux/Mac)
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
cp .env.example .env
# Отредактируйте .env файл

# Запуск приложения
python main.py
```
### Главная ссылка
http://localhost:8000/ ссылка на полный проект с Frontend-частью
#!/usr/bin/env bash
## # setup.sh
## # Basic setup script for Grüblergeist environment and Docker-based PostgreSQL
##
## # 1. Create and activate a virtual environment
## python3 -m venv venv
## source venv/bin/activate
##
## # 2. Install Python dependencies
## pip install --upgrade pip
## pip install -r requirements.txt
##
## # 3. Pull and run PostgreSQL Docker (for local dev); adjust credentials as needed
## docker pull postgres:latest
## docker run --name grueblergeist_db -e POSTGRES_PASSWORD=password -e POSTGRES_USER=user -e POSTGRES_DB=chatdb -p 5432:5432 -d postgres:latest
##
## echo "Setup complete!"
## echo "Please export your OPENAI_API_KEY environment variable before using OpenAI features."
## echo "Usage:"
## echo "  export OPENAI_API_KEY=xxx"
## echo "  ./main.py --mode cli  # or web, evolve, etc."
##
[[ -d grueblergeist-ui ]] && rm -rf grueblergeist-ui
npx create-next-app@latest grueblergeist-ui
pushd grueblergeist-ui || exit 1
npm install axios chart.js react-chartjs-2 tailwindcss postcss autoprefixer
npx tailwindcss init -p
popd

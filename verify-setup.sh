#!/bin/bash

echo "🔍 Verifying Agentic Insight Setup..."
echo "========================================="

# Check if required files exist
echo "📁 Checking project structure..."

required_files=(
    "docker-compose.yml"
    ".env.example"
    "README.md"
    "Makefile"
    "frontend/package.json"
    "frontend/Dockerfile"
    "backend/requirements.txt"
    "backend/Dockerfile"
    "backend/main.py"
    "adx-mcp/requirements.txt"
    "adx-mcp/Dockerfile"
    "adx-mcp/main.py"
    "database/init.sql"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        missing_files+=("$file")
    fi
done

if [[ ${#missing_files[@]} -eq 0 ]]; then
    echo "✅ All required files present"
else
    echo "❌ Missing files:"
    printf '%s\n' "${missing_files[@]}"
    exit 1
fi

# Check if CSV data files exist
echo "📊 Checking test data files..."
csv_files=("sample_data.csv" "TagConfigFormTo_Itera.csv" "itera_data.csv")
for file in "${csv_files[@]}"; do
    if [[ -f "$file" ]]; then
        echo "✅ Found: $file ($(wc -l < "$file") lines)"
    else
        echo "⚠️  Missing: $file"
    fi
done

# Check Docker availability
echo "🐳 Checking Docker..."
if command -v docker &> /dev/null; then
    echo "✅ Docker is installed"
    if docker info &> /dev/null; then
        echo "✅ Docker daemon is running"
    else
        echo "❌ Docker daemon is not running"
        exit 1
    fi
else
    echo "❌ Docker is not installed"
    exit 1
fi

if command -v docker-compose &> /dev/null; then
    echo "✅ Docker Compose is available"
else
    echo "❌ Docker Compose is not available"
    exit 1
fi

# Check environment setup
echo "⚙️  Checking environment..."
if [[ -f ".env" ]]; then
    echo "✅ .env file exists"
    if grep -q "OPENAI_API_KEY=" .env; then
        echo "✅ OpenAI API key configured"
    else
        echo "⚠️  OpenAI API key not configured"
    fi
else
    echo "⚠️  .env file not found. Run: cp .env.example .env"
fi

echo ""
echo "🎯 Setup Summary:"
echo "=================="
echo "✅ Project structure complete"
echo "✅ Docker environment ready"
echo "✅ All service configurations present"
echo ""
echo "📝 Next Steps:"
echo "1. Copy environment file: cp .env.example .env"
echo "2. Edit .env with your OpenAI API key"
echo "3. Start the application: docker-compose up --build"
echo "4. Access the frontend at: http://localhost:3000"
echo ""
echo "🚀 Ready to launch your agentic insight platform!"
import subprocess
import sys

def run_pytest():
    print("📦 Executando testes com pytest...\n")
    result = subprocess.run(["pytest", "tests"], capture_output=False)
    if result.returncode != 0:
        print("\n❌ Alguns testes falharam.")
        sys.exit(result.returncode)
    print("\n✅ Todos os testes passaram com sucesso.")

def run_coverage():
    print("\n📊 Gerando relatório de cobertura...\n")
    subprocess.run(["coverage", "run", "--source=app", "-m", "pytest", "tests"])
    subprocess.run(["coverage", "report", "-m"])
    subprocess.run(["coverage", "html"])
    print("\n📁 Relatório HTML gerado em: htmlcov/index.html")

if __name__ == "__main__":
    args = sys.argv[1:]

    if "--coverage" in args:
        run_coverage()
    else:
        run_pytest()


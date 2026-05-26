"""
Консольное приложение для взаимодействия с RAG ассистентом (ProxiAPI mode).
"""

import sys
import os
import io
from pathlib import Path
from dotenv import load_dotenv
from rag_pipeline import RAGPipeline

# Установить кодировку вывода в UTF-8 для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Загрузка переменных окружения из .env файла
# Ищем .env в корне проекта (на уровень выше)
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    # Пытаемся загрузить из текущей директории
    load_dotenv()


def print_banner():
    """Вывод приветственного баннера."""
    banner = """
========================================
    RAG Assistent (ProxiAPI Mode)
    Retrieval-Augmented Generation
    через ProxiAPI (RU)
========================================
    """
    print(banner)
    print("Vvedite 'exit' ili 'quit' dlya vychoda")
    print("Vvedite 'stats' dlya prosmotra statistiki")
    print("Vvedite 'clear' dlya ochistki kasha\n")


def print_response(result: dict):
    """
    Formatirovannyi vyvod otveta.
    
    Args:
        result: slovar' s rezul'tatom zapроса
    """
    print(f"\n{'-'*60}")
    print(f"Vopros: {result['query']}")
    print(f"{'-'*60}")
    
    # Indikator istochnika otveta
    if result['from_cache']:
        print("Istochnik: KESH")
        if 'cached_at' in result:
            print(f"   Sohraneno: {result['cached_at']}")
    else:
        print(f"Istochnik: ProxiAPI ({result.get('model', 'LLM')})")
        print(f"   Ispolzovano dokumentov: {len(result.get('context_docs', []))}")
    
    print(f"\nOtvet:\n{result['answer']}")
    
    # Pokazat' kontekst (opcional'no)
    if not result['from_cache'] and result.get('context_docs'):
        print(f"\nIspolzovannyi kontekst:")
        for i, doc in enumerate(result['context_docs'][:2], 1):  # Pokazyvaem tol'ko 2 pervyx
            preview = doc['text'][:150] + "..." if len(doc['text']) > 150 else doc['text']
            print(f"   {i}. {preview}")
    
    print(f"{'-'*60}\n")


def print_stats(pipeline: RAGPipeline):
    """
    Vyvod statistiki sistemy.
    
    Args:
        pipeline: ekzempliar RAG pipeline
    """
    stats = pipeline.get_stats()
    
    print(f"\n{'='*60}")
    print("STATISTIKA SISTEMY")
    print(f"{'='*60}")
    
    print("\nVektor'noe hranilishche:")
    print(f"   Kolleciya: {stats['vector_store']['name']}")
    print(f"   Dokumentov: {stats['vector_store']['count']}")
    print(f"   Direktoriya: {stats['vector_store']['persist_directory']}")
    
    print("\nKesh:")
    print(f"   Zapisei: {stats['cache']['total_entries']}")
    print(f"   Razmer BD: {stats['cache']['db_size_mb']:.2f} MB")
    if stats['cache']['oldest_entry']:
        print(f"   Pervaya zapise: {stats['cache']['oldest_entry']}")
    if stats['cache']['newest_entry']:
        print(f"   Poslednyaya zapise: {stats['cache']['newest_entry']}")
    
    print(f"\nModel': {stats['model']}")
    print(f"Rejim: {stats['mode']}")
    print(f"{'='*60}\n")


def main():
    """Glavnaya funkciya prilozheniya."""
    print_banner()
    
    # Proverka naliçiya API URL
    if not os.getenv("PROXI_API_URL"):
        print("Oshibka: peremennaya okruzheniya PROXI_API_URL ne ustanovlena")
        print("\nUstanovite ee sleduyushim obrazom:")
        print("  Windows (PowerShell): $env:PROXI_API_URL='https://your-proxi-api-endpoint.com'")
        print("  Windows (CMD): set PROXI_API_URL=https://your-proxi-api-endpoint.com")
        print("  Linux/Mac: export PROXI_API_URL='https://your-proxi-api-endpoint.com'")
        print("\nIli sozdayte fayl .env v korne proekta s soderzhimym:")
        print("  PROXI_API_URL=https://your-proxi-api-endpoint.com")
        print("\nOpcional'no (esli trebuetsya avtorizaciya):")
        print("  PROXI_API_KEY=your_api_key_here")
        sys.exit(1)
    
    try:
        # Iнициализация RAG pipeline
        print("Iнициализaciya sistemy...\n")
        
        # Poluchenie modeli iz okruzheniya ili ispol'zuem default
        model = os.getenv("PROXI_API_MODEL", "gpt-4o-mini")
        
        pipeline = RAGPipeline(
            collection_name="proxy_rag_collection",
            cache_db_path="proxy_rag_cache.db",
            data_file="data/docs.txt",
            model=model
        )
        print("\nSistema gotova k rabote!\n")
        
    except Exception as e:
        print(f"Oshibka iнициализации: {e}")
        sys.exit(1)
    
    # Osnovnoi tsikl vzaimodeistviya
    while True:
        try:
            # Poluchenie zaprosa ot pol'zovatelya
            user_input = input("Vash vopros: ").strip()
            
            # Obrabotka special'nykh komand
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\nDo svidaniya!")
                break
            
            if user_input.lower() == 'stats':
                print_stats(pipeline)
                continue
            
            if user_input.lower() == 'clear':
                confirm = input("Vy uveren', cto xotite ochistit' kesh? (yes/no): ")
                if confirm.lower() in ['yes', 'y', 'da']:
                    pipeline.cache.clear()
                    print("Kesh ochishchen")
                continue
            
            if not user_input:
                print("Prosim, vvedite vopros\n")
                continue
            
            # Obrabotka zaprosa cherez RAG pipeline
            result = pipeline.query(user_input)
            
            # Vyvod rezul'tata
            print_response(result)
            
        except KeyboardInterrupt:
            print("\n\nPrervano pol'zovatelem. Do svidaniya!")
            break
        except Exception as e:
            print(f"\nOshibka: {e}\n")


if __name__ == "__main__":
    main()

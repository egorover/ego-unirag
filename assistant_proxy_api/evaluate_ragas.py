"""
Скрипт для оценки качества RAG-системы через RAGAS.
Поддержка: ProxiAPI (основной) и OpenAI API (опционально).
Интегрирован из ego-ragascope.
"""

import math
import os
import sys

from datasets import Dataset
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas import evaluate
from ragas.metrics._faithfulness import faithfulness
from ragas.metrics._answer_relevance import answer_relevancy
from ragas.metrics._context_precision import context_precision

import config
from rag_pipeline import RAGPipeline
from utils.console import configure_stdio_utf8
from utils.openai_client import get_langchain_openai_kwargs

configure_stdio_utf8()

# Тестовые вопросы для оценки RAG системы
EVALUATION_QUESTIONS = [
    "Что такое машинное обучение?",
    "Что такое RAG и как он работает?",
    "Какие преимущества использования векторных баз данных?",
]

# Эталонные ответы для метрики context_precision
GROUND_TRUTH_ANSWERS = {
    "Что такое машинное обучение?": "Машинное обучение — это область искусственного интеллекта, которая изучает методы обучения систем на основе данных. Алгоритмы машинного обучения позволяют компьютерам автоматически улучшать свою работу на основе опыта, не требуя явного программирования.",

    "Что такое RAG и как он работает?": "RAG (Retrieval-Augmented Generation) — это архитектура, которая комбинирует извлечение информации и генерацию текста. Система сначала извлекает релевантные документы из базы знаний, затем использует их как контекст для генерации точного ответа на вопрос.",
    
    "Какие преимущества использования векторных баз данных?": "Векторные базы данных обеспечивают эффективный семантический поиск, позволяя находить похожие документы по смыслу, а не только по ключевым словам. Они поддерживают работу с эмбеддингами, обеспечивают быстрый поиск по схожести и масштабируются для больших объёмов данных.",
}


def prepare_dataset(pipeline: RAGPipeline, questions: list[str]) -> Dataset:
    """Подготовка датасета для RAGAS из вопросов."""
    questions_list = []
    answers_list = []
    contexts_list = []
    ground_truths_list = []
    
    print("\n[*] Получение ответов от RAG системы...\n")

    for i, question in enumerate(questions, 1):
        print(f"  {i}/{len(questions)}: {question}")
        
        result = pipeline.query(question, use_cache=False)
        
        questions_list.append(question)
        answers_list.append(result["answer"])
        contexts_list.append([chunk["text"] for chunk in result["context_docs"]])
        ground_truths_list.append(GROUND_TRUTH_ANSWERS.get(question, ""))

    return Dataset.from_dict(
        {
            "question": questions_list,
            "answer": answers_list,
            "contexts": contexts_list,
            "ground_truth": ground_truths_list,
        }
    )


def _build_metrics():
    """Собирает метрики RAGAS с учётом выбранного API-провайдера."""
    langchain_config = get_langchain_openai_kwargs()

    if config.API_PROVIDER == "openai":
        os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY
    else:
        os.environ["OPENAI_API_KEY"] = config.PROXY_API_KEY
        os.environ["OPENAI_API_BASE"] = config.PROXY_API_URL

    try:
        from ragas.llms import llm_factory
        from ragas.embeddings import LangchainEmbeddingsWrapper
        from openai import OpenAI
        from langchain_openai import OpenAIEmbeddings as LangchainOpenAIEmbeddings

        print("\n[*] Создаём OpenAI клиент...")
        openai_client = OpenAI(
            api_key=os.environ["OPENAI_API_KEY"],
            base_url=os.environ.get("OPENAI_API_BASE"),
        )

        print(f"[*] Создаём LLM: {config.CHAT_MODEL}...")
        ragas_llm = llm_factory(
            model=config.CHAT_MODEL,
            provider="openai",
            client=openai_client,
            temperature=0,
        )

        print(f"[*] Создаём эмбеддинги: {config.EMBEDDING_MODEL}...")
        langchain_embeddings = LangchainOpenAIEmbeddings(
            model=config.EMBEDDING_MODEL,
            **langchain_config,
        )
        ragas_embeddings = LangchainEmbeddingsWrapper(langchain_embeddings)

        print("[*] Инициализируем метрики...")
        # Инициализируем метрики с кастомными LLM и embeddings
        faithfulness.llm = ragas_llm
        faithfulness.embeddings = ragas_embeddings
        answer_relevancy.llm = ragas_llm
        answer_relevancy.embeddings = ragas_embeddings
        context_precision.llm = ragas_llm
        context_precision.embeddings = ragas_embeddings

        print("[OK] Метрики успешно созданы!\n")
        return [
            faithfulness,
            answer_relevancy,
            context_precision,
        ]

    except Exception as exc:
        print(f"[WARN] Ошибка создания метрик через llm_factory: {exc}")
        print("[WARN] Используем метрики без кастомизации LLM/эмбеддингов\n")
        return [faithfulness, answer_relevancy, context_precision]


def _metric_values(result, name: str) -> list[float]:
    """Извлекает числовые значения метрики из результата RAGAS."""
    try:
        values = result[name]
    except (KeyError, TypeError):
        values = getattr(result, name, [])
    return [v for v in values if not math.isnan(v)]


def evaluate_rag_system() -> None:
    """Оценка RAG-системы по предопределённым вопросам."""
    print("=" * 70)
    print("ОЦЕНКА КАЧЕСТВА RAG-СИСТЕМЫ (PROXIAPI MODE) ЧЕРЕЗ RAGAS")
    print("=" * 70)
    print(f"Используемый провайдер: {config.API_PROVIDER.upper()}")

    # Инициализация RAG pipeline
    try:
        print("\n[*] Инициализация RAG системы (ProxiAPI mode)...\n")
        
        # Используем абсолютный путь к файлу документов
        script_dir = Path(__file__).parent
        docs_file = script_dir / "data" / "docs.txt"
        
        pipeline = RAGPipeline(
            collection_name="proxy_rag_collection",
            cache_db_path="proxy_rag_cache.db",
            data_file=str(docs_file),
            model=config.CHAT_MODEL
        )
        print(f"\n[OK] RAG система готова к оценке (модель: {config.CHAT_MODEL})\n")
    except Exception as e:
        print(f"[ОШИБКА] Ошибка инициализации RAG pipeline: {e}")
        sys.exit(1)

    dataset = prepare_dataset(pipeline, EVALUATION_QUESTIONS)

    print("\n" + "=" * 70)
    print("\n[*] Запуск оценки метрик...")
    print("Метрики: faithfulness, answer_relevancy, context_precision")

    metrics_to_use = _build_metrics()
    
    # Запускаем оценку без column_map (поля датасета имеют правильные имена)
    print("\n[*] Выполнение оценки (это займёт 1-3 минуты)...\n")
    result = evaluate(
        dataset=dataset,
        metrics=metrics_to_use,
        raise_exceptions=False,
    )

    print("\n" + "=" * 70)
    print("РЕЗУЛЬТАТЫ ОЦЕНКИ")
    print("=" * 70)

    faithfulness_values = _metric_values(result, "faithfulness")
    answer_relevancy_values = _metric_values(result, "answer_relevancy")
    context_precision_values = _metric_values(result, "context_precision")

    avg_faithfulness = (
        sum(faithfulness_values) / len(faithfulness_values)
        if faithfulness_values
        else 0.0
    )
    avg_answer_relevancy = (
        sum(answer_relevancy_values) / len(answer_relevancy_values)
        if answer_relevancy_values
        else float("nan")
    )
    avg_context_precision = (
        sum(context_precision_values) / len(context_precision_values)
        if context_precision_values
        else 0.0
    )

    print()
    print("[МЕТРИКИ] Средние значения:")
    print(f"  Faithfulness (верность ответа):       {avg_faithfulness:.4f}")
    
    if not math.isnan(avg_answer_relevancy):
        print(f"  Answer Relevancy (релевантность):   {avg_answer_relevancy:.4f}")
    else:
        print(
            "  Answer Relevancy (релевантность): "
            "не удалось вычислить (ошибка с эмбеддингами)"
        )
    print(f"  Context Precision (точность контекста): {avg_context_precision:.4f}")
    
    # Вычисляем и выводим средний балл
    valid_scores = [s for s in [avg_faithfulness, avg_answer_relevancy, avg_context_precision] 
                    if not math.isnan(s) and s > 0]
    if valid_scores:
        avg_score = sum(valid_scores) / len(valid_scores)
        print(f"\n{'─'*70}")
        print(f"[ИТОГО] Средний балл: {avg_score:.4f}")
        
        if avg_score >= 0.7:
            print("    Оценка: Отличное качество! [OK]")
        elif avg_score >= 0.5:
            print("    Оценка: Удовлетворительное качество [!]")
        else:
            print("    Оценка: Требует улучшения [X]")

    print("\n" + "=" * 70)
    print("ДЕТАЛИ ПО ВОПРОСАМ")
    print("=" * 70)

    for i, question in enumerate(EVALUATION_QUESTIONS):
        print(f"\n{i + 1}. {question}")
        try:
            f_val = result["faithfulness"][i]
            if math.isnan(f_val):
                print("    Faithfulness: не удалось вычислить")
            else:
                print(f"    Faithfulness: {f_val:.4f}")
        except (KeyError, TypeError, IndexError, ValueError):
            print("    Faithfulness: ошибка вычисления")

        try:
            ar_val = result["answer_relevancy"][i]
            if math.isnan(ar_val):
                print("    Answer Relevancy: не удалось вычислить")
            else:
                print(f"    Answer Relevancy: {ar_val:.4f}")
        except (KeyError, TypeError, IndexError, ValueError):
            print("    Answer Relevancy: ошибка вычисления")

        try:
            cp_val = result["context_precision"][i]
            if math.isnan(cp_val):
                print("    Context Precision: не удалось вычислить")
            else:
                print(f"    Context Precision: {cp_val:.4f}")
        except (KeyError, TypeError, IndexError, ValueError):
            print("    Context Precision: ошибка вычисления")

    print("\n" + "=" * 70)
    print("[OK] Оценка завершена!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    from pathlib import Path
    evaluate_rag_system()

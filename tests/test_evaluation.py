import pytest

from llm_tutor.evaluation import evaluate_answer, validate_tasks


def test_evaluate_answer_accepts_symbolically_equivalent_fraction():
    assert evaluate_answer("ANALYSIS... Final Result: [[1/2]]", "0.5") == 1


def test_evaluate_answer_requires_all_components_of_system_solution():
    assert evaluate_answer("Final Result: [[x=2]]", "x=2 and y=3") == 0
    assert evaluate_answer("Final Result: [[x=2 and y=3]]", "x=2 and y=3") == 1


def test_evaluate_answer_rejects_missing_result_delimiters():
    assert evaluate_answer("The answer is 17", "17") == 0


def test_validate_tasks_requires_75_tasks_and_15_balanced_categories():
    tasks = [
        {
            "id": category * 5 + offset,
            "category": f"category-{category}",
            "content": "2 + 2",
            "expected_result": "4",
            "solution_steps": "2 + 2 = 4",
        }
        for category in range(15)
        for offset in range(5)
    ]
    assert validate_tasks(tasks) == {"task_count": 75, "category_count": 15}


def test_validate_tasks_rejects_duplicate_ids():
    tasks = [
        {"id": 1, "category": "derivatives", "content": "x", "expected_result": "x"},
        {"id": 1, "category": "integrals", "content": "x", "expected_result": "x"},
    ]
    with pytest.raises(ValueError, match="unique"):
        validate_tasks(tasks)

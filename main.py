import json
import os
from deadlock_solver import DeadlockSystem
from visualizer import plot_resource_allocation_graph
def load_config(filepath: str) -> DeadlockSystem:
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return DeadlockSystem(
        processes=data['processes'],
        resources=data['resources'],
        allocation=data['allocation'],
        max_matrix=data['max'],
        available=data['available'],
        request=data.get('request', None)
    )
def main():
    config_dir = "configs"
    configs = sorted([f for f in os.listdir(config_dir) if f.endswith('.json')])
    print("=== Программный комплекс исследования тупиковых ситуаций ===")
    print("Выберите конфигурацию:")
    for idx, cfg in enumerate(configs, 1):
        print(f"[{idx}] {cfg}")
    choice = int(input("\nНомер конфигурации: ")) - 1
    selected_file = os.path.join(config_dir, configs[choice])
    system = load_config(selected_file)
    print(f"\n--- Анализ конфигурации: {configs[choice]} ---")
    # 1. Банкир: проверка безопасности
    is_safe, seq = system.is_safe_state()
    print(f"\n1. Алгоритм банкира:")
    if is_safe:
        print(f"   [+] Состояние БЕЗОПАСНОЕ. Безопасная последовательность: {' -> '.join(seq)}")
    else:
        print("   [-] Состояние НЕБЕЗОПАСНОЕ (потенциальный риск взаимоблокировки).")
    # 2. Обнаружение дедлоков
    has_deadlock, deadlocked = system.detect_deadlock()
    print(f"\n2. Обнаружение тупиков на графе:")
    if has_deadlock:
        print(f"   [!] ТУПИК ОБНАРУЖЕН! Заблокированные процессы: {', '.join(deadlocked)}")
        
        # 3. Восстановление
        costs = [50 + i * 25 for i in range(system.n)] # Условные вычисления (CPU ticks)
        print(f"\n3. Сравнение стратегий восстановления (Затраты вычислений: {dict(zip(system.processes, costs))}):")
        rec = system.simulate_recovery(costs)
        print(f"   * Стратегия завершения (Termination):")
        print(f"     Убиты процессы: {rec['termination']['procs']}, Потери вычислений: {rec['termination']['lost_cost']} тиков")
        print(f"   * Стратегия вытеснения (Preemption с чекпоинтами):")
        print(f"     Вытеснены процессы: {rec['preemption']['procs']}, Потери вычислений: {rec['preemption']['lost_cost']} тиков")
    else:
        print("   [+] Активных тупиков нет. Все запросы могут быть удовлетворены.")
    # Визуализация
    show_graph = input("\nПостроить граф распределения ресурсов? (y/n): ")
    if show_graph.lower() == 'y':
        plot_resource_allocation_graph(system, title=f"RAG: {configs[choice]}")
if __name__ == '__main__':
    main()
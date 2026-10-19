import copy
from typing import List, Dict, Tuple, Optional
class DeadlockSystem:
    def __init__(self, processes: List[str], resources: List[str],
                 allocation: List[List[int]], max_matrix: List[List[int]],
                 available: List[int], request: Optional[List[List[int]]] = None):
        self.processes = processes
        self.resources = resources
        self.n = len(processes)
        self.m = len(resources)
        
        self.allocation = copy.deepcopy(allocation)
        self.max = copy.deepcopy(max_matrix)
        self.available = copy.deepcopy(available)
        
        # Need = Max - Allocation
        self.need = [
            [self.max[i][j] - self.allocation[i][j] for j in range(self.m)]
            for i in range(self.n)
        ]
        
        # Request matrix (если не задан явно, по умолчанию равен Need)
        self.request = copy.deepcopy(request) if request is not None else copy.deepcopy(self.need)
    # --- 1. Алгоритм банкира: Безопасность состояния ---
    def is_safe_state(self) -> Tuple[bool, List[str]]:
        work = list(self.available)
        finish = [False] * self.n
        safe_seq = []
        while len(safe_seq) < self.n:
            found = False
            for i in range(self.n):
                if not finish[i]:
                    # Проверяем Need_i <= Work
                    if all(self.need[i][j] <= work[j] for j in range(self.m)):
                        for j in range(self.m):
                            work[j] += self.allocation[i][j]
                        finish[i] = True
                        safe_seq.append(self.processes[i])
                        found = True
                        break
            if not found:
                break
        is_safe = all(finish)
        return is_safe, safe_seq
    # --- 1. Алгоритм банкира: Запрос ресурсов ---
    def request_resources(self, p_idx: int, req_vec: List[int]) -> Tuple[bool, str, List[str]]:
        # 1. req <= need
        if any(req_vec[j] > self.need[p_idx][j] for j in range(self.m)):
            return False, f"Ошибка: Процесс {self.processes[p_idx]} превысил заявленный максимум!", []
        # 2. req <= available
        if any(req_vec[j] > self.available[p_idx] for j in range(self.m)):
            return False, f"Процесс {self.processes[p_idx]} должен ждать: ресурсов недостаточно.", []
        # Пробное выделение
        orig_avail = list(self.available)
        orig_alloc = copy.deepcopy(self.allocation)
        orig_need = copy.deepcopy(self.need)
        for j in range(self.m):
            self.available[j] -= req_vec[j]
            self.allocation[p_idx][j] += req_vec[j]
            self.need[p_idx][j] -= req_vec[j]
        safe, seq = self.is_safe_state()
        if safe:
            return True, f"Запрос удовлетворен. Система в безопасном состоянии.", seq
        else:
            # Откат
            self.available = orig_avail
            self.allocation = orig_alloc
            self.need = orig_need
            return False, "Запрос отклонен: перевод в небезопасное состояние (риск тупика).", []
    # --- 2. Обнаружение тупиков (алгоритм для нескольких экземпляров) ---
    def detect_deadlock(self) -> Tuple[bool, List[str]]:
        work = list(self.available)
        finish = [False] * self.n
        for i in range(self.n):
            if all(self.allocation[i][j] == 0 for j in range(self.m)):
                finish[i] = True
        while True:
            found = False
            for i in range(self.n):
                if not finish[i]:
                    if all(self.request[i][j] <= work[j] for j in range(self.m)):
                        for j in range(self.m):
                            work[j] += self.allocation[i][j]
                        finish[i] = True
                        found = True
                        break
            if not found:
                break
        deadlocked_procs = [self.processes[i] for i in range(self.n) if not finish[i]]
        has_deadlock = len(deadlocked_procs) > 0
        return has_deadlock, deadlocked_procs
    # --- 3. Сравнение стратегий восстановления ---
    def simulate_recovery(self, cpu_costs: List[int]) -> Dict:
        """
        cpu_costs: условные затраты вычислений, совершенные процессом к текущему моменту
        Стратегия 1: Поочередное завершение процессов (Process Termination) по минимуму затрат
        Стратегия 2: Вытеснение ресурсов (Resource Preemption) с откатом минимально затратного процесса
        """
        has_deadlock, deadlocked = self.detect_deadlock()
        if not has_deadlock:
            return {"status": "No deadlock detected"}
        # 1. Termination strategy: убиваем процессы из deadlock-набора по возрастанию потерь
        deadlock_indices = [i for i in range(self.n) if self.processes[i] in deadlocked]
        sorted_by_cost = sorted(deadlock_indices, key=lambda idx: cpu_costs[idx])
        term_lost_cost = 0
        terminated_procs = []
        sim_sys = copy.deepcopy(self)
        for p_idx in sorted_by_cost:
            terminated_procs.append(sim_sys.processes[p_idx])
            term_lost_cost += cpu_costs[p_idx]
            # Освобождаем ресурсы убитого процесса
            for j in range(sim_sys.m):
                sim_sys.available[j] += sim_sys.allocation[p_idx][j]
                sim_sys.allocation[p_idx][j] = 0
                sim_sys.request[p_idx][j] = 0
            still_deadlocked, _ = sim_sys.detect_deadlock()
            if not still_deadlocked:
                break
        # 2. Preemption strategy: частичный откат (забираем только занятые ресурсы у жертвы,
        # штраф принимаем как 60% от его вычислений из-за чекпоинта)
        preempt_lost_cost = 0
        preempted_procs = []
        sim_sys2 = copy.deepcopy(self)
        for p_idx in sorted_by_cost:
            preempted_procs.append(sim_sys2.processes[p_idx])
            # Предположим наличие чекпоинтов: теряется 60% работы
            preempt_lost_cost += int(cpu_costs[p_idx] * 0.6)
            for j in range(sim_sys2.m):
                sim_sys2.available[j] += sim_sys2.allocation[p_idx][j]
                sim_sys2.allocation[p_idx][j] = 0
                # Запрос остается активным, процесс ждет
            still_deadlocked, _ = sim_sys2.detect_deadlock()
            if not still_deadlocked:
                break
        return {
            "termination": {
                "procs": terminated_procs,
                "lost_cost": term_lost_cost
            },
            "preemption": {
                "procs": preempted_procs,
                "lost_cost": preempt_lost_cost
            }
        }
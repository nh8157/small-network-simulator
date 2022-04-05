class DependencyGraph:
    def __init__(self):
        self.first = Node(True, [], [])
        self.last = Node(False, [], [])
        self.current_task = [self.first]
        self.first.add_next(self.last)
        self.last.add_prev(self.first)
        self.first.update_status(True)

    def add_node(self, prev_val: list, val, next_val: list) -> bool:
        node = Node(val, [], [])
        prev_nodes = [self.find_node(v, self.first) for v in prev_val]
        next_nodes = [self.find_node(v, self.first) for v in next_val]
        for p in prev_nodes:
            p.add_next(node)
            node.add_prev(p)
            if p == self.first:
                p.update_self_dependency
            for n in next_nodes:
                if self.is_directly_connected(p, n):
                    p.rmv_next(n)
                    n.rmv_prev(p)
        for n in next_nodes:
            node.add_next(n)
            n.add_prev(node)
        return True
    def find_node(self, node, graph):
        if graph.get_val() == node:
            return graph
        for n in graph.get_next():
            found = self.find_node(node, n)
            if found != None:
                return found
    def get_ready_task(self):
        ready_task = []
        for t in self.current_task:
            if t.get_dependency_status():
                ready_task.append(t)
        return ready_task
    def mark_task_done(self, val):
        node = self.find_node(val, self.first)
        node.update_status(True)
        node.update_next_dependency()
        next = node.get_next()
        for n in next:
            if n not in self.current_task:
                self.current_task.append(n)
        self.current_task.remove(node)
    def is_directly_connected(self, n1, n2):
        return (n1 in n2.get_prev()) and (n2 in n1.get_next())

class Node:
    def __init__(self, val, prev=[], next=[]):
        self.val = val
        self.status = False
        self.dependency = False
        self.dependency_ctr = 0
        self.prev = prev
        self.next = next
    def get_val(self):
        return self.val
    def get_prev(self):
        return self.prev
    def get_next(self) -> list:
        return self.next
    def get_status(self):
        return self.status
    def get_dependency_status(self):
        return self.dependency
    def pretty_print_next(self):
        l = self.get_next()
        val = [v.get_val() for v in l]
        print(val)
    def update_status(self, status):
        self.status = status
    def update_self_dependency(self):
        self.dependency_ctr += 1
        if self.dependency_ctr == len(self.prev):
            self.dependency = True
    def update_next_dependency(self):
        for i in self.next:
            i.update_self_dependency()
    def add_prev(self, prev_node):
        self.prev.append(prev_node)
    def add_next(self, next_node):
        self.next.append(next_node)
    def rmv_prev(self, prev_node):
        self.prev.remove(prev_node)
    def rmv_next(self, next_node):
        self.next.remove(next_node)

if __name__ == '__main__':
    dg = DependencyGraph()
    dg.add_node([True], 10, [False])
    dg.add_node([True], 20, [10])
    dg.add_node([20], 30, [10])
    dg.add_node([20], 50, [10])
    dg.add_node([20], 60, [10])
    dg.add_node([20], 110, [60])
    dg.add_node([10], 90, [False])
    dg.add_node([True], 100, [20])
    next = [dg.first]
    while next != []:
        new_next = []
        for i in next:
            print(str(i.get_val()) + "\t", end='')
            new_next.extend(i.get_next())
        next = new_next
        print()
    dg.mark_task_done(True)
    tasks = dg.get_ready_task()
    dg.mark_task_done(100)
    tasks = dg.get_ready_task()
    dg.mark_task_done(20)
    tasks = dg.get_ready_task()
    dg.mark_task_done(30)
    tasks = dg.get_ready_task()
    dg.mark_task_done(50)
    tasks = dg.get_ready_task()
    print(tasks[0].get_val())
    dg.mark_task_done(110)
    tasks = dg.get_ready_task()
    dg.mark_task_done(60)
    tasks = dg.get_ready_task()
    dg.mark_task_done(10)
    dg.mark_task_done(90)
    tasks = dg.get_ready_task()
    print(tasks[0].get_val())

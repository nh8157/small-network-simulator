class Tree:
    def __init__(self, procedure=None):
        self.procedure = procedure
        self.root = Node()
        if procedure != None:
            self.level = len(procedure) + 1
        else:
            self.level = None

    def set_procedure(self, proc):
        self.procedure = proc[:]

    def get_procedure(self):
        return self.procedure[:]
    
    def get_root(self):
        return self.root

    def create_tree_wrapper(self):
        self.create_tree(self.get_root(), self.get_procedure())
    
    def create_tree(self, node, proc):
        # construct the tree
        for i in range(len(proc)):
            new_child = Node(proc[i], node)
            node.add_child(new_child)
            proc_copy = proc[:]
            proc_copy[-1], proc_copy[i] = proc_copy[i], proc_copy[-1]
            proc_copy.pop()
            self.create_tree(new_child, proc_copy)

    def print_tree_wrapper(self):
        self.print_tree([self.get_root()])

    def print_tree(self, node):
        child = []
        for i in node:
            print(i.get_command(), end="")
            child.extend(i.get_child())
        print()
        if len(child):
            self.print_tree(child)

    def dfs_wrapper(self):
        r = self.get_root()
        self.dfs(r)

    def dfs(self, node):
        print(node.get_command())
        for i in node.get_child():
            self.dfs(i)
    
    def prune_tree(self):
        pass



class Node:
    def __init__(self, command=None, pred=None):
        self.command = command
        self.pred = pred
        self.child = []
        self.valid = False

    def add_pred(self, pred):
        self.pred = pred

    def add_child(self, *child):
        for i in child:
            self.child.append(i)

    def get_command(self):
        return self.command

    def get_pred(self):
        return self.pred

    def get_child(self):
        return self.child[:]
    
    def print_child(self):
        c = self.get_child()
        for i in c:
            print(i.get_command())

def main():
    t = Tree(['a', 'b', 'c'])
    t.create_tree_wrapper()
    t.print_tree_wrapper()
    # t.dfs_wrapper()
    
if __name__ == '__main__':
    main()
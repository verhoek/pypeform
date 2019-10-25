from collections import defaultdict

_ref_index = {}
lookup = {}
answers = []


class Action(object):
    def __init__(self, source, target, condition):
        self.source = source
        self.target = target
        self.condition = condition
        self.relevant = condition['op'] != 'always'


class ActionGraph(object):
    def __init__(self):
        self._map = defaultdict(list)

    def add(self, source_ref, target_ref, condition):
        source_idx = _ref_index[source_ref].index
        self._map[source_idx].append(Action(source_ref, target_ref, condition))

    def peers(self, index, with_children=False):
        relevant_actions = filter(lambda x: x.relevant, self._map[index])

        return ','.join([peer.index for peer in self.get_all_children(index, with_children)])

    def get_all_children(self, index, with_children=False):

        peers = []

        stack = [lookup[index]]

        while stack:
            popped_field = stack.pop()

            if popped_field.index != index and popped_field not in peers:
                peers.append(popped_field)

            for action in filter(lambda x: x.relevant, self._map[popped_field.index]):
                field = _ref_index[action.target]
                stack.append(field)

            if popped_field.next_within_group:
                stack.append(popped_field.next_within_group)

            if not with_children:
                continue

            for field in popped_field.children:
                stack.append(field)
                for action in filter(lambda x: x.relevant, self._map[field.index]):
                    stack.append(_ref_index[action.target])

        return peers


class Field(object):
    def __init__(self, index, **kwargs):
        self.ref = kwargs['ref']
        self.text = kwargs['title']
        self.type = kwargs['type']
        self.index = index
        self.properties = kwargs

        self.category = None
        self.answer = None
        self.children = []

        # within a field group, knowing the next sibling is relevant information
        self.next_within_group = None
        _ref_index[self.ref] = self
        lookup[self.index] = self

    def get_main_idx(self):
        return self.index.split('.')[0] if '.' in self.index else self.index

    def has_sub_fields(self):
        """
        Has subfields seems to be equivalent to having type=group.
        :return:
        """
        return 'properties' in self.properties and 'fields' in self.properties['properties']

    def __str__(self):
        return f'{self.index} ) {self.text} ({self.ref})'


class Answer(object):
    def __init__(self, **kwargs):
        self._ref = kwargs['field']['ref']
        self.field = _ref_index[self._ref]
        self.field.answer = self
        self.type = kwargs['type']

        if self.type == 'choice':
            self.response = kwargs[self.type]['label']
        elif self.type == 'choices':
            self.response = ','.join(kwargs[self.type]['labels'])
        else:
            self.response = kwargs[self.type]

        answers.append(self)

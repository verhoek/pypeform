from collections import defaultdict
from typing import Dict, Any, List

answers = []


class Field(object):

    lookup: Dict[str, Any] = {}
    ref_index = {}
    counter = 1

    def __init__(self, index, **kwargs):
        self.ref = kwargs['ref']
        self.text = kwargs['title']
        self.type = kwargs['type']
        self.index = index
        self.properties = kwargs
        self.id = Field.counter
        Field.counter += 1

        self.category = None
        self.answer = None
        self.children = []

        # within a field group, knowing the next sibling is relevant information
        self.next_within_group = None
        Field.ref_index[self.ref] = self
        Field.lookup[self.index] = self


    def get_main_idx(self):
        return self.index.split('.')[0] if '.' in self.index else self.index

    def has_sub_fields(self):
        """
        Has subfields seems to be equivalent to having type=group.
        :return:
        """
        return 'properties' in self.properties and 'fields' in self.properties['properties']

    @classmethod
    def set_categories(cls, category_data: Dict[str, List[str]]) -> None:
        """
        Set categories of all fields using a dictionary indexed by categories and values
        a list of indices of associated fields.

        :param category_data:
        :return:
        """
        for field in cls.lookup.values():
            idx = field.get_main_idx()
            for category in filter(lambda x: idx in category_data[x], category_data.keys()):
                field.category = category
                break

    def __str__(self):
        return f'{self.index} ) {self.text} ({self.ref})'


class Answer(object):

    submitted_timestamp = None

    def __init__(self, **kwargs):
        self._ref = kwargs['field']['ref']
        self.field = Field.ref_index[self._ref]
        self.field.answer = self
        self.type = kwargs['type']

        if self.type == 'choice':
            self.response = kwargs[self.type]['label']
        elif self.type == 'choices':
            self.response = ','.join(kwargs[self.type]['labels'])
        else:
            self.response = kwargs[self.type]

        answers.append(self)


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
        source_idx = Field.ref_index[source_ref].index
        self._map[source_idx].append(Action(source_ref, target_ref, condition))

    def peers(self, field: Field, limit=-1, with_children=False):
        relevant_actions = filter(lambda x: x.relevant, self._map[field.index])

        return self._get_all_children(field, limit, with_children)

    def _get_all_children(self, field, limit, with_children):

        peers = []

        stack = [field]

        while stack and (len(stack) < limit or limit == -1):
            popped_field = stack.pop()

            if popped_field.index != field.index and popped_field not in peers:
                peers.append(popped_field)

            for action in filter(lambda x: x.relevant, self._map[popped_field.index]):
                field = Field.ref_index[action.target]
                stack.append(field)

            if popped_field.next_within_group:
                stack.append(popped_field.next_within_group)

            if not with_children:
                continue

            for field in popped_field.children:
                stack.append(field)
                for action in filter(lambda x: x.relevant, self._map[field.index]):
                    stack.append(Field.ref_index[action.target])

        return peers

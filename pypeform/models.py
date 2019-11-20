from collections import defaultdict
from typing import Dict, Any, List


class Category(object):

    categories = []

    def __init__(self):
        self.ids : List = None
        Category.categories.append(self)

    def update_fields(self) -> None:
        """
        Set categories of all fields using a dictionary indexed by categories and values
        a list of indices of associated fields.

        :param category_data:
        :return:
        """
        for field in Field.lookup.values():
            if not field.get_parent_index() in self.ids:
                continue
            field.category = self


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

    def get_parent_index(self):
        return self.index.split('.')[0] if '.' in self.index else self.index

    def has_sub_fields(self):
        """
        Has subfields seems to be equivalent to having type=group.
        :return:
        """
        return 'properties' in self.properties and 'fields' in self.properties['properties']

    def get_sub_fields(self):
        return self.properties['properties']['fields']

    def __str__(self):
        return f'{self.index} ) {self.text} ({self.ref})'


class Answer(object):
    answers = []

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

        Answer.answers.append(self)


class Condition(object):
    def __init__(self, op, name):
        self.op = op
        self.name = name


class Action(object):
    _actions = defaultdict(list)

    def __init__(self, source, target, condition):
        self.source = source
        self.target = target
        self.condition = condition
        self.not_always = condition.op != 'always'
        self.in_category = condition.name == 'category'

        Action._actions[source].append(self)

    @staticmethod
    def get_actions():
        for actions in Action._actions.values():
            for action in actions:
                yield action

#
# class ActionGraph(object):
#     def __init__(self):
#         self.map = defaultdict(list)
#
#     def add_by_ref(self, source_ref, target_ref, condition):
#         self.map[source_ref].append(Action(source_ref, target_ref, condition))
#
#     def add_by_index(self, source_idx, target_idx, condition):
#         source_ref = Field.lookup[source_idx].ref
#         target_ref = Field.lookup[target_idx].ref
#         self.add_by_ref(source_ref, target_ref, condition)
#
#     def peers(self, field: Field, limit=-1, with_children=False):
#
#         return self._get_all_children(field, limit, with_children)
#
#     def _get_all_children(self, root_field, limit, with_children):
#
#         peers = []
#
#         stack = [root_field]
#
#         while stack and (len(stack) < limit or limit == -1):
#             popped_field = stack.pop()
#
#             if not popped_field.category or not popped_field.category.graph:
#                 continue
#
#             if popped_field.index != root_field.index and popped_field not in peers:
#                 peers.append(popped_field)
#
#             for action in filter(lambda x: x.not_always, self.map[popped_field.ref]):
#                 field = Field.ref_index[action.target]
#                 stack.append(field)
#
#             if popped_field.next_within_group:
#                 stack.append(popped_field.next_within_group)
#
#             if not with_children:
#                 continue
#
#             for field in popped_field.children:
#                 stack.append(field)
#                 for action in filter(lambda x: x.not_always, self.map[field.ref]):
#                     stack.append(Field.ref_index[action.target])
#
#         return peers

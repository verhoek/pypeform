from .models import Answer, Field, ActionGraph
from typing import List, Dict


def _depth_first_search(field: Field):
    stack = [field]

    while stack:
        field = stack.pop()

        print(field)

        if not field.has_sub_fields():
            continue

        num = 0

        prev_field = None
        for sub_field_raw in field.properties['properties']['fields']:
            if sub_field_raw['type'] != 'statement':
                index = f'{chr(97 + num)}'
                num += 1
            else:
                # usually this does not occur
                index = f'statement-{chr(97 + num)}'

            sub_field = Field(f'{field.index}.{index}', **sub_field_raw)

            if prev_field:
                prev_field.next_within_group = sub_field

            prev_field = sub_field
            field.children.append(sub_field)
            stack.append(sub_field)


def parse_fields(fields_raw: dict):
    num = 1
    for field_raw in fields_raw:
        if field_raw['type'] != 'statement':
            index = num
            num += 1
        else:
            index = f'statement-{num}'
        _depth_first_search(Field(f'{index}', **field_raw))

    return Field.lookup


def _parse_logic(logic_raw: dict):
    for logic in logic_raw:
        source_ref = logic['ref']

        for action in logic['actions']:
            action_type = action['action']
            if action_type != 'jump':
                # unsupported if not jump
                continue

            target_ref = action['details']['to']['value']
            condition = action['condition']
            yield source_ref, target_ref, condition


def create_action_graph(logic: dict) -> ActionGraph:
    graph = ActionGraph()

    for source_ref, target_ref, condition in _parse_logic(logic):
        graph.add(source_ref, target_ref, condition)

    return graph


def parse_form_response(form_response: dict):
    submitted_timestamp = form_response['form_response']['submitted_at']
    answers = []
    for answer_raw in form_response['form_response']['answers']:
        answers.append(Answer(**answer_raw))

    return answers



from .models import Answer, Field, ActionGraph, lookup


def depth_first_search(field: Field):
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
        depth_first_search(Field(f'{index}', **field_raw))


def parse_logic(logic_raw: dict):
    for logic in logic_raw:
        source_ref = logic['ref']

        for action in logic['actions']:
            action_type = action['action']
            if action_type != 'jump':
                # unsupported if not jump
                continue

            target_ref = action['details']['to']['value']
            condition = action['condition']
            graph.add(source_ref, target_ref, condition)


def set_categories(category_data):
    for field in lookup.values():
        idx = field.get_main_idx()
        for category in filter(lambda x: idx in category_data[x], category_data.keys()):
            field.category = category
            break


def parse_answers(survey_response):
    submitted_timestamp = survey_response['form_response']['submitted_at']
    answers = []
    for answer_raw in survey_response['form_response']['answers']:
        answers.append(Answer(**answer_raw))

    return answers


graph = ActionGraph()

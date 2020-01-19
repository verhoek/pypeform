from .models import Answer, Field, Category, Condition, Action, FieldConfig
from typing import List, Dict


def _depth_first_search(field: Field):
    stack = [field]

    while stack:
        field = stack.pop()

        if not field.has_sub_fields():
            continue

        num = 0

        prev_field = None
        # within group
        for sub_field_raw in field.get_sub_fields():
            index_letter = chr(ord('a') + num)
            if sub_field_raw['type'] != 'statement':
                num += 1
            else:
                index_letter = f'statement-{index_letter}'

            sub_field = Field(f'{field.index}.{index_letter}', **sub_field_raw)

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


def parse_categories(category_data):
    for category_info in category_data:
        category = Category()
        category.name = category_info['name']
        category.id = category_info['id']
        category.field_ids = category_info['field_ids']
        category.color = category_info['color'] if 'color' in category_info else None
        category.graph = category_info['graph'] if 'graph' in category_info else True
        category.update_fields()


def parse_actions(logic: dict) -> None:
    # chain following questions within a category to a link
    for field in Field.lookup.values():
        category = field.category

        if not category:
            continue

        n = len(category.field_ids)
        i = category.field_ids.index(field.get_parent_index())

        # no circular references
        if i == n - 1:
            continue

        target_idx = category.field_ids[(i + 1) % n]
        target_ref = Field.lookup[target_idx].ref
        Action(field.ref, target_ref, Condition(None, 'category'))

    for source_ref, target_ref, condition in _parse_logic(logic):
        Action(source_ref, target_ref, Condition(condition['op'], None))


def parse_form_response(form_response: dict):
    Answer.submitted_timestamp = form_response['form_response']['submitted_at']
    answers = []
    for answer_raw in form_response['form_response']['answers']:
        answers.append(Answer(**answer_raw))

    return answers


def parse_field_config(field_config_data):
    """
    :param field_config_data:

    an array of the objects, where objects are like
    {
      "selector": {
        "field_id": "2",
        "response": {
          "type": "exact",
          "value": "some value"
        }
      },
      "size": 100
    }
    :return:
    """
    for config in field_config_data:

        field_id = config['selector'].get('field_id')
        if field_id:
            field_ids = [field_id]
        else:
            field_ids = config['selector'].get('field_ids')

        for field_id in field_ids:
            field = Field.lookup.get(field_id, None)

            if not field:
                continue

            if 'response' in config['selector']:
                if not field.answer:
                    continue

                if config['selector']['response']['type'] == "exact":
                    x = field.answer.response
                    y = config['selector']['response']['value']
                    if isinstance(x, str) and isinstance(y, str):
                        if x.lower() != y.lower():
                            continue
                    elif x != y:
                        continue

                if (config['selector']['response']['type'] == "pattern" and
                    config['selector']['response']['value']) != "*":
                    continue

                if (config['selector']['response']['type'] == "not" and
                    config['selector']['response']['value']) == field.answer.response:
                    continue

            field.config = FieldConfig()
            field.config.size = config.get('size', None)
            field.config.color = config.get('color', None)

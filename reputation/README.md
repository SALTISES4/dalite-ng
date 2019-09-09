# Adding a new criterion

## Implementation
- Add a new file in `models/criteria/criteria/`
- Implement a model inheriting from `model.criterion.criterion.Criterion`
  - This model needs to have a `name` field, `info` static method and `evaluate` method (see `min_words` for an example)
- Add this model to all the `__init__.py` files until `models/__init__.py`
- Add the model to `model/criterion/criterion_list.py`
- Add the model to `admin.py`

## Adding a criterion to a reputation
- Add the criterion through the `UsesCriterion` model
- The `name` corresponds to the `name` field of the model inheriting `Criterion` and `version` to whichever version of it you want

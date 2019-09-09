import factory

from peerinst.models import Assignment


class AssignmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Assignment

    identifier = factory.Faker("word")
    title = factory.Faker("sentence", nb_words=4)

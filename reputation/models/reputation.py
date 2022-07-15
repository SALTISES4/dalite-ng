import json
from datetime import date as date_

from django.db import IntegrityError, models

from ..logger import logger
from .reputation_type import ReputationType


class Reputation(models.Model):
    reputation_type = models.ForeignKey(
        ReputationType, on_delete=models.CASCADE
    )

    def __str__(self):
        try:
            reputation_model = self.reputation_model
        except ValueError:
            reputation_model = "Unknown"
        return "{} for {}: {}".format(
            self.pk, self.reputation_type, reputation_model
        )

    def evaluate(self, criterion=None):
        """
        Returns the reputation of the linked model as a tuple of the quality
        and the different criterion results.

        Parameters
        ----------
        criterion : Optional[str] (default : None)
            Name of the criterion for which reputation is calculated. If None,
            evaluates for all criteria

        Returns
        -------
        Optional[float]
            Quality of the answer or None if no criteria present
        Either
            List[Dict[str, Any]]
                If `criterion` is None, individual criteria under the format
                    [{
                        name: str
                        full_name: str
                        description: str
                        version: int
                        weight: int
                        reputation: float
                    }]
            Dict[str, Any]
                If `criterion` is specified, details under the format
                    {
                        name: str
                        full_name: str
                        description: str
                        version: int
                        weight: int
                        reputation: float
                    }

        Raises
        ------
        ValueError
            If this reputation doesn't correspond to any type of reputation
        ValueError
            If the given criterion isn't part of the list for this reputation
            type
        """
        try:
            reputation_model = self.reputation_model
        except ValueError:
            return None, []
        return self.reputation_type.evaluate(reputation_model, criterion)

    @property
    def reputation_model(self):
        """
        Returns the model corresponding to this instance.

        Returns
        -------
        Model
            Model instance

        Raises
        ------
        ValueError
            If this reputation doesn't correspond to any type of reputation
        """
        try:
            return getattr(self, self.reputation_type.model_name)
        except AttributeError:
            msg = (
                "This reputation is associated with a "
                "reputation type using the model {}".format(
                    self.reputation_type.model_name
                )
            )
            logger.error(msg)
            raise ValueError(msg)

    @staticmethod
    def create(cls):
        """
        Creates an instance of Reputation.

        Parameters
        ----------
        cls : Union[str, object]
            Model class for which to create the instance. Converted to string
            if object passed

        Returns
        -------
        Reputation
            Created instance

        Raises
        ------
        TypeError
            If the `cls` isn't a string
        ReputationType.DoesNotExist
            If there is no reputation type for the given class
        """
        if not isinstance(cls, str):
            cls = cls.__class__.__name__

        reputation_type = ReputationType.objects.get(type=cls.lower())

        return Reputation.objects.create(reputation_type=reputation_type)


class ReputationHistory(models.Model):
    reputation = models.ForeignKey(
        Reputation, editable=False, on_delete=models.CASCADE
    )
    date = models.DateField(auto_now_add=True)
    reputation_value = models.FloatField(null=True, blank=True, editable=False)
    reputation_details = models.TextField(editable=False)

    class Meta:
        unique_together = ("reputation", "date")

    @staticmethod
    def create(reputation):
        value, details = reputation.evaluate()
        try:
            instance = ReputationHistory.objects.create(
                reputation=reputation,
                reputation_value=value,
                reputation_details=json.dumps(details),
            )
        except IntegrityError:
            instance = ReputationHistory.objects.get(
                reputation=reputation, date=date_.today()
            )
            instance.reputation_value = value
            instance.reputation_details = json.dumps(details)
            instance.save()

        return instance

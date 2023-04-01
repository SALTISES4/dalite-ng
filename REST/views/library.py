from .views import CollectionViewSet


class TeacherCollectionLibraryViewSet(CollectionViewSet):
    def get_queryset(self):
        # TODO: Update related name in Collection model
        return self.request.user.teacher.followers.all()

        #  + Collection.objects.filter(
        #     owner=self.request.user.teacher
        # ).order_by(
        #     "-last_modified"
        # )

from brewtils.models import Principal, Operation

from mongoengine.queryset.visitor import Q


def create_mongo_query(
    current_user: Principal = None,
    filter_garden: bool = True,
    filter_namespace: bool = True,
):
    """
    Creates custom query logic for MongoDB
    Args:
        current_user: Principal record associated with the Operation

    Returns: Q query arg

    """

    mongo_query = None
    for permission in current_user.permissions:
        if (
            permission.garden is not None
            and (permission.namespace is None or not filter_namespace)
            and filter_garden
        ):
            if mongo_query:
                mongo_query = mongo_query | Q(garden=permission.garden)
            else:
                mongo_query = Q(garden=permission.garden)
        elif (
            (permission.garden is None or not filter_garden)
            and permission.namespace is not None
            and filter_namespace
        ):
            if mongo_query:
                mongo_query = mongo_query | Q(garden=permission.namespace)
            else:
                mongo_query = Q(garden=permission.namespace)
        elif (
            permission.garden is not None
            and permission.namespace is not None
            and filter_garden
            and filter_namespace
        ):
            if mongo_query:
                mongo_query = mongo_query | (
                    Q(garden=permission.namespace) & Q(garden=permission.garden)
                )
            else:
                mongo_query = Q(garden=permission.namespace) & Q(
                    garden=permission.garden
                )

    return mongo_query


def operation_db_filtering(obj: Operation = None, current_user: Principal = None):
    """
    Injects custom filtering to reduce return from DB calls

    Args:
        obj: Operation model to be modified
        current_user: Principal record associated with the Operation

    Returns:

    """
    if obj.operation_type in ["REQUEST_COUNT", "REQUEST_READ_ALL"]:
        if "filter_args" not in obj.kwargs:
            obj.kwargs["filter_args"] = list()

        obj.kwargs["filter_args"].append(create_mongo_query(current_user=current_user))


obj_db_filtering = {
    "OperationSchema": operation_db_filtering,
}


def model_db_filter(obj=None, current_user: Principal = None):
    """
    Injects custom DB logic into model to improve filtering
    Args:
        obj: Model to filter
        current_user: Principal record associated with the Model

    Returns:

    """

    # Impossible to add filters, so we return the object
    if not hasattr(obj, "schema"):
        return

    # Garden access gets them Read to everything, so no filtering
    # for permission in current_user.permissions:
    #     if permission.garden == config.get("garden.name") and permission.namespace is None:
    #         return

    if obj.schema in obj_db_filtering.keys():
        obj_db_filtering[obj.schema](obj=obj, current_user=current_user)

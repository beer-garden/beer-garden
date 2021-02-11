from brewtils.models import Principal, Operation


def operation_db_filtering(obj: Operation = None, current_user: Principal = None):
    """
    Injects custom filtering to reduce return from DB calls

    Args:
        obj: Operation model to be modified
        current_user: Principal record associated with the Operation

    Returns:

    """
    if "REQUEST_COUNT" == obj.operation_type:
        if "namespace__in" not in obj.kwargs:
            obj.kwargs["namespace__in"] = list()
        for permission in current_user.permissions:
            obj.kwargs["namespace__in"].append(permission.namespace)

    elif "REQUEST_READ_ALL" == obj.operation_type:
        if "filter_params" not in obj.kwargs:
            obj.kwargs["filter_params"] = {}
        if "namespace__in" not in obj.kwargs["filter_params"]:
            obj.kwargs["filter_params"]["namespace__in"] = list()
        for permission in current_user.permissions:
            obj.kwargs["filter_params"]["namespace__in"].append(permission.namespace)


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

    # Local access gets them Read to everything, so no filtering
    for permission in current_user.permissions:
        if permission.is_local:
            return

    if obj.schema in obj_db_filtering.keys():
        obj_db_filtering[obj.schema](obj=obj, current_user=current_user)

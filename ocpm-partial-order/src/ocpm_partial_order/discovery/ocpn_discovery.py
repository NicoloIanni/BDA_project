import pm4py


def discover_ocpn(ocel):
    """
    Scopre una Object-Centric Petri Net a partire da un OCEL.
    """
    return pm4py.discover_oc_petri_net(ocel)
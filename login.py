# modeled off of: https://github.com/openshift/openshift-client-python/blob/main/examples/login.py
# login with oc or login with the cli
# def cli_login(kubeconfig: str, server: str, token: str, timeout_seconds: int = 60 * 30) -> int:
#     """
#     Log into an OpenShift cluster using openshift_client's Context.
#     If login fails, print the 'err' message from the JSON.
#     """
#     my_context = Context()
#     my_context.kubeconfig_path = kubeconfig
#     my_context.api_server = server
#     my_context.token = token

#     with oc.timeout(60 * 30), oc.tracking() as t, my_context:
#         if oc.get_config_context() is None:
#             print(f'Current context not set. Attempting to log onto API server: {my_context.api_server}\n')
#             try:
#                 oc.invoke('login')
#             except OpenShiftPythonException:
#                 # login failed, print error message
#                 tracking_result = t.get_result().as_dict()
                
#                 action_error = None
#                 for action in tracking_result.get('actions', []):
#                     if action.get('verb') == 'login' and not action.get('success'):
#                         action_error = action.get('err', 'An unknown error occurred during login.')
#                         break
                
#                 print('Login failed.')
#                 if action_error:
#                     # Print ONLY the specific 'err' message from the action
#                     print(action_error.strip()) 
                
#                 exit(1)

#         print(f'Current context: {oc.get_config_context()}')




    # p_login = sub.add_parser("login", help="Log into an OpenShift cluster")
    # p_login.add_argument("-k", "--kubeconfig", required=True, help="oc kubeconfig")
    # p_login.add_argument("-s", "--server", required=True, help="API server URL")
    # p_login.add_argument("-t", "--token", required=True, help="Login token (e.g., oc whoami -t)")
'''Watches AWS metadata API for spot termination notices on spot nodes.
Uses kubectl to drain nodes once their termination notice is present.'''

from os import getenv
from time import sleep
from subprocess import call
from requests import get, put


def main():
    '''Watch for termination notices on spot instance nodes on AWS'''
    print('Starting up')

    node_name = getenv('NODE_NAME')

    drain_parameters = getenv('DRAIN_PARAMETERS', '--grace-period=120 --force --ignore-daemonsets')

    print('Watching for termination notice on node %s' % node_name)

    counter = 0

    while True:
        sleep(15)
        url = "http://169.254.169.254/latest/api/token"
        headers = {"X-aws-ec2-metadata-token-ttl-seconds": "180"}
        token_response = put(url, headers=headers)

        if token_response.status_code == 200:
            token = token_response.text
            headers = {"X-aws-ec2-metadata-token": token}
            response = get("http://169.254.169.254/latest/meta-data/spot/termination-time", headers=headers)

            if response.status_code == 200:
                kube_command = ['kubectl', 'drain', node_name]
                kube_command += drain_parameters.split()

                print("Draining node: %s" % node_name)
                result = call(kube_command)
                if result == 0:
                    print('Node Drain successful')
                    break
            else:
                if counter == 60:
                    counter = 0
                    print("Termination notice status: %s, on Node: %s" %
                        (response.status_code, node_name)
                        )
                counter += 5
                sleep(5)
        else:
            print("No Token: %s" %
                (token_response.status_code)
                )


if __name__ == '__main__':
    main()

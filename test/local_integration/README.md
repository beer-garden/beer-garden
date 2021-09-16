# Local Integration Tests for BeerGarden

*WARNING: this is beta software. It probably has a number of bugs. Comments and bug reports are welcome.*

1. USAGE:
   
    ```bash
    ./integration_tests.py --help
    usage: integration_tests [-h]
                             [--test [{all,scheduler,local_plugins,remote_plugins,gardens_stomp,stomp_,gardens_http} [{all,scheduler,local_plugins,remote_plugins,gardens_stomp,stomp_,gardens_http} ...]]]
                             beer_garden_path brewtils_path
    
    Run BeerGarden integration tests locally.
    
    positional arguments:
      beer_garden_path      The path to the top-level directory of the beer garden sources
      brewtils_path         The path to the top-level directory of the brewtils sources
    
    optional arguments:
      -h, --help            show this help message and exit
      --test [{all,scheduler,local_plugins,remote_plugins,gardens_stomp,stomp_,gardens_http} [{all,scheduler,local_plugins,remote_plugins,gardens_stomp,stomp_,gardens_http} ...]]
                            Test suites to run (default: all)
    ```
    
    If the `--test` switch is omitted or if the `--test`switch has no argument or if `all` is one of the arguments, all integration tests will be run. Alternately, one or more of `scheduler, local_plugins, remote_plugins, gardens_stomp, stomp_, gardens_http`can be provided, separated by spaces, and only those tests suites will be run.
    
2. NOTE: It currently takes a bit less that 11 minutes to run all integration tests with the tool, including building the Docker image. This is faster than the approximately 30 minutes the GitHub action takes, which is only scheduled to run at midnight.

3. DISCUSSION: The script uses libraries to imitate running `docker` and `docker-compose` from the command line. The tool provides a Docker image to mount in local versions of `beer_garden` and `brewtils`and then run `beer_garden` in that image, with the example plugins being pulled down from GitHub.

    The main `beer_garden` image and a child `beer_garden` are run alongside `mongodb`, `activemq`, and`rabbitmq`, though no  `ui` instance is run because it not yet needed by the integration tests.

    The tool provides the necessary config files for all of the images to communicate with each other in the way the integration tests expect. It also sets environment variables that allow the tests to run. After the tests are run, the images, the network and associated volumes are torn down, but other Docker images, unrelated to this tool, can be running at the same time and they will not be touched.

4. WARNING: The Docker image setup is quite fragile. At this time, we use the SHA1 of the commit that the *master* branch of the *example_plugins* repo points to. This is a workaround until such time that a proper release can be created (there is an open issue on GitHub for this). If everything suddenly breaks, this is a good starting point for troubleshooting.

5. RUNNING WITHOUT THE TOOL: The Python script itself makes running a great number of integration tests all at once easy. However, most of the magic is in the configuration files and the workflow can be run by hand without using the Python script:

    a. If the tool has never been run the Docker image has to be built first. From the directory where the python script resides, run

    ```bash
    docker build -t beer_garden_integration_tests .
    ```

    b. To run `docker-compose`, several environment variables need to be created, namely the paths to the top-level directories of the `beer_garden` and `brewtils` source repos and paths to the parent and child config files. Also, it may be necessary to prune the docker volumes not in use:

    ```bash
    APP_SRC=/home/user/src/beer_garden \
    BREWTILS_SRC=/home/user/src/brewtils \
    PARENT_CONFIG=`pwd`/configs/config.yaml \
    CHILD_CONFIG=`pwd`/configs/config-child.yaml \
    docker-compose -f docker-compose-local-integration-tests.yml down \
    && docker volume prune -f \
    && APP_SRC=/home/user/src/beer_garden \
    BREWTILS_SRC=/home/user/src/brewtils \
    PARENT_CONFIG=`pwd`/configs/config.yaml \
    CHILD_CONFIG=`pwd`/configs/config-child.yaml \
    docker-compose -f docker-compose-local-integration-tests.yml up -d
    ```

    c. If the previous commands had no problems, then `beer_garden` and friends will be running in containers. `pytest` can then be run from the local machine with the addition of a couple of environment variables, for example:

    ```bash
    BG_HOST=localhost BG_SSL_ENABLED=false pytest ../integration/gardens_stomp/setup/garden_setup_test.py::TestGardenSetup::test_garden_manual_register_successful
    ```

6. ASSUMPTIONS:

    a. The script *integration_tests.py* is in a directory that is a sibling of the top level directory of the integration tests. Currently everything resides in the`local_integration`directory inside the top-level `test` directory:

    ```bash
    test
    ├── conf
    ├── integration
    └── local_integration
    ```

    If the script or the integration tests are moved, the code will need to be changed in order to find the directories holding the tests.
    b. The user has access to the `brewtils` source code repo somewhere on the system
    c. The user can run `docker`from the command line. 

7. FILES

    ```bash
    ├── Dockerfile                                   -- sets up the Python environment for beer_garden
    ├── README.md                                    -- this file
    ├── configs                                      -- config files needed by beer_garden
    │   ├── app-logging.yaml                            	(these can be edited to change the behavior
    │   ├── config-child.yaml                           	of the beer_garden instances, however, their
    │   ├── config.yaml                                 	current state is what is needed by the tests)
    │   └── plugin-logging.yaml
    ├── docker-compose-local-integration-tests.yml  -- the Docker compose file to bring up the network
    ├── integration_tests.py                        -- the Python script for this tool
    ├── requirements-dev.txt                        -- additional libraries needed to run this tool
    └── requirements.txt                            -- the Python libraries need by Brewtils
    ```

8. TODO:

    a. Allow specific tests to be run ala `pytest`, e.g. `integration_tests.py --test scheduler --run_only TestClass::specific_test`

    b. Refactor/rewrite existing integration tests and add new integration tests in such a way that the entire process in much simpler, thus allowing this tool to hopefully be simplified.

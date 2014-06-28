This project is useful if you are using a routed network on your docker bridge and want DNS resolution for your containers.  
  
Only handles "A" and "NS" queries.  
For "NS" queries we respond with the IP-address of the machine running docker-dns, this is so we can handle a subdomain with docker-dns.  
For every "A" query we will look through all running containers and see if any of them have the hostname that was requested and respond with the IP of the container.  
  
== Quickstart ==  
docker run -d --net=host -v /var/run/docker.sock:/var/run/docker.sock larsla/docker-dns  
  
== Options (passed in via -e parameters to docker) ==  
=== DOCKER_HOST ===  
Default: unix://var/run/docker.sock  
Tell docker-dns how to connect to docker.  
  
=== INTERFACE ===  
Default: eth0  
Which interface we will use the IP of when responding to NS queries.  

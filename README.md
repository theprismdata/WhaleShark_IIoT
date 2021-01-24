![issue badge](https://img.shields.io/github/issues/dataignitelab/WhaleShark_IIoT)
![forks badge](https://img.shields.io/github/forks/dataignitelab/WhaleShark_IIoT)
![starts badge](https://img.shields.io/github/stars/dataignitelab/WhaleShark_IIoT)
![license badge](https://img.shields.io/github/license/dataignitelab/WhaleShark_IIoT)

## Abount Project: Equipment Monitor system for Smart Factory or Smart Farm
WhaleShark IIoT(혹은 M2M) 프로젝트는 스마트 팩토리, 로보틱스를 위한 어픈소스 기반 모니터링 시스템 입니다.
 - 주 데이터 수집 대상
   - 다양한 센서와 연결된 설비들과 연결 됩니다.
WhaleShark IIoT, an open source monitoring system for smart factories, is a IIoT-based process monitoring system.
 - Target Object
   - Equipment connected to various sensors

## How to Run
- 수행 환경
  - Python3, Redis, RabbitMQ, Influxdb
- Run Environment
  - Python3, Redis, RabbitMQ, Influxdb
  
- Step 1: 설치 간편화를 위해 Docker를 설치하기 바랍니다. 운영체제에 따라 설치 방법이 다릅니다.
- Step 1: Please install Docker on your system for easy setup
- Step 2: 다음의 명령으로 Redis 컨터네이를 실행 합니다.
- Step 2: Run redis container
   - docker pull redis
     docker run --name whaleshark-redis -d -p 6379:6379 redis
     만약 컨터이너 이미지가 존재하지만 종료된 경우 다음의 명령으로 다시 활성화 시킵니다.
     if container is exist
        docker restart  whaleshark-redis
- Step 3: RabbitMQ 컨터이너슬 실행합니다.     
- Step 3: Run rabbitmq container
   - docker run -d --hostname whaleshark --name whaleshark-rabbit -p 5672:5672 -p 8080:15672 -e RABBITMQ_DEFAULT_USER=whaleshark -e RABBITMQ_DEFAULT_PASS=whaleshark rabbitmq:3-management
     만약 RabbitMQ 컨테이너가 존재하나 종료된 경우 다음 명령으로 다시 활성화 시킵니다.
     if container is exist
        docker restart  whaleshark-rabbit

- Step 4: IIoT 데이터 전송 에이전트의 데이터를 수신하기 위해 다음의 명령으로 수집 서버를 동작 시킵니다.
- Step 4: Run next script to sensor data collection server(like DAQ) with IIoT Data broadcasting agent.
  whalesharkM2M 폴더로 이동 후 아래의 명령 실행
  python3 M2MServer.py

- Step 5: Influx 연동을 위해 다음의 명령을 실행합니다.
- Step 5: Run next script to sync Influxdb
  python3 TSDBAgent.py
  
- Step 6: 직렬 포트로 설비와 연결된 시스템(Windows or Linux)에서 다음의 명령으로 IIoT 에이전트를 수행합니다.
- Step 6: Run next scipt to run IIoT agent on your system(windows or linux) has connection with serial port
  python3 M2MClient.py 

- 추가 중요 정보
- Ubuntu 18.04 버전에서 InfluxDB 설치
  - 저장소를 추가합니다.
  sudo curl -sL https://repos.influxdata.com/influxdb.key | sudo apt-key add -
  sudo echo "deb https://repos.influxdata.com/ubuntu bionic stable" | sudo tee /etc/apt/sources.list.d/influxdb.list
  - 라이브러리를 업데이트 하고 influxdb를 설치합니다.
  sudo apt update
  sudo apt install influxdb
  - influxdb를 동작 시키고 상태를 확인합니다.
  sudo systemctl start influxdb
  sudo systemctl status influxdb
  - influx cli에 접속합니다.
  shell>influx
  
- Important information
  - 이 버전에서는 설비의 정보를 시스템의 직렬포트를 이용하여 획득합니다. 때문에 설비의 상태 정보를 얻기 위해서 Memory 정보가 필요할 것입니다. 이 정보는 whalesharkM2M/config/controllerinfo.csv에 저장되어 있습니다. 여러분의 설비에 환경을 맞추기 위해서는 controllerinfo.csv의 STATIONID, ADDRESS를 수정해야 합니다. 연동과 관련된 문의 사항은 Issues,Discussion에 등록하여 주시기 바랍니다.
  - In last version, We using serial port to collect facility status information. So, You will need memory map setup to get status formation. The information stored in whalesharkM2M/config/controllerinfo.csv. For setting up your facility environment, you have to edit fields(STATIONID, ADDRESS) on controllerinfo.csv.
    Please register other question about sync Issues, Discussion
    Thank you. Good luck.

### API
 https://whaleshark-iiot.readthedocs.io/en/latest/

## Download
 - [Last Release] https://github.com/theprismdata/WhaleShark_IIoT

import requests
import time

url = 'http://localhost:8000'
def start(user_key, problem_id, number_of_elevators):
    uri = url+"/start/"+user_key+"/"+str(problem_id)+"/"+str(number_of_elevators)
    return requests.post(uri).json()

def oncalls(token):
    uri = url+'/oncalls'
    return requests.get(uri, headers={'X-Auth-Token':token}).json()

def action(token, commands):
    # commands  -   [ {elevator 0}, {elevator 1}..]
    uri = url+'/action'
    return requests.post(uri, headers={'X-Auth-Token':token}, json={'commands':commands})

class Elevator():
    def __init__(self):
        self.floor = 1
        self.passengers = []
        self.status = "STOPPED"
        self.calls = []
        self.src = self.dest = 0
        self.isStarted = False
    # candidates are decided outside the function
    def add_call(self, call):
        if self.src == 0 and self.dest == 0:
            self.src = call['start']
            self.dest = call['end']
        self.calls.append(call)
    def decide_action(self):
        #일단 시작점으로
        if not self.isStarted and not self.src == self.dest:
            if self.floor < self.src:
                self.status = "UPWARD"
                self.floor += 1
                return "UP"
            elif self.floor > self.src:
                self.status = "DOWNWARD"
                self.floor -= 1
                return "DOWN"
            else:
                self.status = "STOPPED"
                self.isStarted = True
                return "STOP"

        # 탈 사람, 내릴 사람
        to_enter = [call for call in self.calls if call['start']==self.floor]
        to_exit = [call for call in self.passengers if call['end']==self.floor]

        # 내리거나 타야할 층에 도착
        if (self.status == "UPWARD" or self.status == "DOWNWARD") and (to_enter or to_exit):
            self.status = "STOPPED"
            return "STOP"
        # 문을 연다
        elif self.status == "STOPPED" and (to_enter or to_exit):
            self.status = "OPEND"
            return "OPEN"
        # 열려있고 아직 탈 사람이 있다
        elif self.status == "OPEND" and to_enter:
            ret = dict()
            self.passengers.extend(to_enter)
            self.calls = [call for call in self.calls if call not in to_enter]
            ret["ENTER"] = [x['id'] for x in to_enter]
            return ret
        # 열려있고 아직 내릴 사람이 있다
        elif self.status == "OPEND" and to_exit:
            ret = dict()
            self.passengers = [passenger for passenger in self.passengers if passenger not in to_exit]
            ret["EXIT"] = [x['id'] for x in to_exit]
            return ret
        # 열려있고 다 내렸다
        elif self.status == "OPEND" and not (to_enter or to_exit):
            self.status = "STOPPED"
            if self.floor == self.dest:
                self.src = self.dest = 0
                self.isStarted = False
            return "CLOSE"
        # 한 번의 여정이 끝났다.
        elif self.src == self.dest:
            return "STOP"
        # 타거나 내리려는 사람 없이 이동중
        else:
            #print("what is this : ",self.src, self.dest, self.floor, self.status)
            if self.src < self.dest:
                self.status = "UPWARD"
                self.floor += 1
                return "UP"
            else:
                self.status = "DOWNWARD"
                self.floor -= 1
                return "DOWN"

if __name__ == '__main__':
    # API START
    elevator_num = 4
    start_ret = start('zzaebok', 2, elevator_num)
    token = start_ret['token']
    already_taken = []
    elevators = [Elevator() for _ in range(elevator_num)]
    # LOOP
    while True:
        #time.sleep(0.01)
        # If it is finished, break
        oncalls_ret = oncalls(token)
        if oncalls_ret['is_end']: break
        not_taken = [call for call in oncalls_ret['calls'] if call not in already_taken]
        commands = []
        for i, elevator in enumerate(elevators):
            # if remained call is adequate, then enter them
            num_jobs = len(elevator.passengers) + len(elevator.calls)
            if num_jobs < 8 and not_taken:
                if elevator.src == elevator.dest:
                    elevator.add_call(not_taken[0])
                    already_taken.append(not_taken[0])
                    not_taken.pop(0)
                # ascending
                elif elevator.isStarted and elevator.src < elevator.dest:
                    ascending_job = [call for call in not_taken if elevator.floor < call['start'] < call['end'] < elevator.dest]
                    for call in ascending_job[:min(8-num_jobs, len(ascending_job))]:
                        elevator.add_call(call)
                        already_taken.append(call)
                        not_taken.remove(call)
                # descending
                elif elevator.isStarted and elevator.src > elevator.dest:
                    descending_job = [call for call in not_taken if elevator.dest < call['end'] < call['start'] < elevator.floor]
                    for call in descending_job[:min(8-num_jobs, len(descending_job))]:
                        elevator.add_call(call)
                        already_taken.append(call)
                        not_taken.remove(call)
            # check status and do action
            elevator_ret = elevator.decide_action()
            #enter or exit
            if type(elevator_ret) == dict:
                if "ENTER" in elevator_ret:
                    commands.append({'elevator_id':i, 'command':"ENTER", 'call_ids':elevator_ret["ENTER"]})
                if "EXIT" in elevator_ret:
                    commands.append({'elevator_id': i, 'command': "EXIT", 'call_ids': elevator_ret["EXIT"]})
            else:
                commands.append({'elevator_id':i, 'command':elevator_ret})
        try:
            action_ret = action(token, commands)
        except:
            print(acion_ret)
        #print("Action: ", commands)
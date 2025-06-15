#!/bin/bash

proj_path="/home/desktop/jc-dev/jiancheng" 
server_path="/home/desktop/jc-dev/img_server"


tmux start-server
tmux new-session -d -s session
tmux split-window -d "cd $proj_path/frontend/jiancheng && npm run dev -- --host"
tmux split-window -d
tmux select-pane -t session:0.1
tmux send-keys -t session:0.1 "cd $proj_path/backend-python && gunicorn --bind localhost:8000 --timeout 60 wsgi:app --access-logfile -" C-m
tmux split-window -d
tmux select-pane -t session:0.2
tmux send-keys -t session:0.2 "cd $server_path && python3 -m http.server 12667" C-m
tmux select-pane -t session:0.0
tmux attach
#cd $proj_path
#pwd

#tmux new-session -d "cd frontend/jiancheng/ && npm run dev -- --host"
#cd ~
#tmux split-window -d 

#tmux split-window -d "cd $server_path && python3 -m http.server 12667"
#tmux split-window -d "redis-server"




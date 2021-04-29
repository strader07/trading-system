# error
while :; do
    clear
    echo 'errors: '
    kubectl get pods | ag error | wc -l
    sleep 60
done

# pending
while :; do
    clear
    echo 'pending: '
    kubectl get pods | ag pending | wc -l
    sleep 60
done

# running
while :; do
    clear
    echo 'running: '
    kubectl get pods | ag '2019|2020' | ag running | wc -l
    sleep 60
done

# completed
while :; do
    clear
    echo 'completed: '
    kubectl get pods | ag complete | wc -l
    sleep 60
done

# top pods
while :; do clear; kubectl top pod --sort-by=memory | grep tardis | head -n 10; sleep 300; done
while :; do clear; kubectl top pod --sort-by=memory | grep -v tardis | head -n 10; sleep 300; done

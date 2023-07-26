const on_btn = document.getElementById('power_updater')
const runSimple_btn = document.getElementById('advBtn')
const runAdv_btn = document.getElementById('simpleBtn')
const backup_btn = document.getElementById('foo')
let listener
let off_btn = document.getElementById('updater_stop')

window.addEventListener('load',monitorThreads)

listener.addEventListener('thread_count',(e)=>{
    console.log(e.data)
    thread_counter.innerHTML = e.data
    if (Number(e.data) >0){
        status.innerHTML = 'true'
        
    } else {
        status.innerHTML = 'false'
    }
})
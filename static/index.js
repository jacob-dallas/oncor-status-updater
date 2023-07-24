const onBtnPwr = document.getElementById('power_updater_start')
const offBtnPwr = document.getElementById('power_updater_stop')
const onBtnRad = document.getElementById('radar_updater_start')
const offBtnRad = document.getElementById('radar_updater_stop')

const runSimple_btn = document.getElementById('advBtn')
const runAdv_btn = document.getElementById('simpleBtn')
const backup_btn = document.getElementById('foo')


let ip = location.host

window.addEventListener('load',monitorThreads)

function monitorThreads(){

    listener = new EventSource(`http://${ip}/monitor_threads`)

    listener.onopen = (e)=>{
        console.log('starting!')
    }

    let powerThread_counter = document.getElementById('power_thread_count')
    let powerStatus = document.getElementById('power_thread_status')
    let radarThread_counter = document.getElementById('radar_thread_count')
    let radarStatus = document.getElementById('radar_thread_status')
    let cond1=false
    let cond2=false
    
    listener.addEventListener('power_thread_count',(e)=>{
        powerThread_counter.innerHTML = e.data
        if (Number(e.data) >0){
            powerStatus.innerHTML = 'Online'
            cond1=false
            onBtnPwr.style.display = 'none'
            offBtnPwr.style.display = 'block'
        } else {
            powerStatus.innerHTML = 'Offline'
            onBtnPwr.style.display = 'block'
            offBtnPwr.style.display = 'none'
            cond1=true
            if (cond2){
                listener.close()
            }
        }
    })
    listener.addEventListener('radar_thread_count',(e)=>{
        radarThread_counter.innerHTML = e.data
        if (Number(e.data) >0){
            radarStatus.innerHTML = 'Online'
            cond2=false
            onBtnRad.style.display = 'none'
            offBtnRad.style.display = 'block'
        } else {
            radarStatus.innerHTML = 'Offline'
            onBtnRad.style.display = 'block'
            offBtnRad.style.display = 'none'
            cond2=true
            if (cond1){
                listener.close()
            }
        }
    })
    listener.addEventListener('close',(e)=>{
        powerThread_counter.innerHTML = 0
        powerStatus.innerHTML = 'Offline'
        onBtnPwr.style.display = 'block'
        offBtnPwr.style.display = 'none'

        radarThread_counter.innerHTML = 0
        radarStatus.innerHTML = 'Offline'
        onBtnRad.style.display = 'block'
        offBtnRad.style.display = 'none'
        listener.close()
    })
}
offBtnPwr.addEventListener('click',async ()=>{
    let powerThread_counter = document.getElementById('power_thread_count')
    let powerStatus = document.getElementById('power_thread_status')
    onBtnPwr.style.display = 'block'
    offBtnPwr.style.display = 'none'
    powerThread_counter.innerHTML = 0
    powerStatus.innerHTML = 'Offline'
    let res = await fetch(`http://${ip}/stop_threads?thread=power`,{
        method: 'POST'
    })
    console.log(res)
    // check and make sure threads are closed on the server
})
offBtnRad.addEventListener('click',async ()=>{
    let radarThread_counter = document.getElementById('radar_thread_count')
    let radarStatus = document.getElementById('radar_thread_status')
    onBtnRad.style.display = 'block'
    offBtnRad.style.display = 'none'
    radarThread_counter.innerHTML = 0
    radarStatus.innerHTML = 'Offline'
    let res = await fetch(`http://${ip}/stop_threads?thread=radar`,{
        method: 'POST'
    })
})


const startModal = document.getElementById('thread_config')

onBtnPwr.addEventListener('click',()=>{
    startModal.showModal()
    startModal.endUrl = `http://${ip}/start_power_threads`
})
onBtnRad.addEventListener('click',()=>{
    startModal.showModal()
    startModal.endUrl = `http://${ip}/start_radar_threads`
})

startModal.addEventListener("click", e => {
    const dialogDimensions = startModal.getBoundingClientRect()
    if (
      e.clientX < dialogDimensions.left ||
      e.clientX > dialogDimensions.right ||
      e.clientY < dialogDimensions.top ||
      e.clientY > dialogDimensions.bottom
    ) {
        startModal.close()
    }
  })

let formSelector = document.getElementById('run_type')

let recordOpt = document.getElementById('recordOpt')
recordOpt.addEventListener('change',(e)=>{
    let recordInt = document.getElementById('recordInt')
    if (e.target.checked){
        recordInt.disabled = false
    } else{
        recordInt.disabled = true
    }
})

let recordOptAdv = document.getElementById('recordOptAdv')
recordOptAdv.addEventListener('change',(e)=>{
    let recordInt = document.getElementById('recordIntAdv')
    if (e.target.checked){
        recordInt.disabled = false
    } else{
        recordInt.disabled = true
    }
})


formSelector.addEventListener('change',(e)=>{
    simpleForm = document.getElementById('simpleForm')
    advancedForm = document.getElementById('advancedForm')
    if(e.target.value == 1 ){
        simpleForm.style.display = 'block'
        advancedForm.style.display = 'none'
    } else{
        simpleForm.style.display = 'none'
        advancedForm.style.display = 'block'    
    }
})

let runUntilOpt = document.getElementById('runUntilOpt')
let runForOpt = document.getElementById('runForOpt')

runForOpt.addEventListener('change',(e)=>{
    let until = document.getElementById('runUntilInput')
    let forInput = document.getElementById('runForInput')
    until.style.display = 'none'
    forInput.style.display = 'block'
    until.disabled = true
    forInput.disabled = false
})

runUntilOpt.addEventListener('change',(e)=>{
    let until = document.getElementById('runUntilInput')
    let forInput = document.getElementById('runForInput')
    until.style.display = 'block'
    forInput.style.display = 'none'
    until.disabled = false
    forInput.disabled = true
})

async function submitThreadConf(){
    let form
    if (formSelector.value ==1){
        form = document.getElementById('simpleForm')
    } else {
        form = document.getElementById('advancedForm')
    }
    const data = new FormData(form)
    data.append('pause',true)
    
    res = await fetch(
        startModal.endUrl,
        {
            body: data,
            method: 'POST',
        }
    )
    console.log(res)
    monitorThreads()
}
runAdv_btn.addEventListener('click',submitThreadConf)
runSimple_btn.addEventListener('click',submitThreadConf)
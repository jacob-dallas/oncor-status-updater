const on_btn = document.getElementById('power_updater')
const backup_btn = document.getElementById('foo')
let listener
let off_btn = document.getElementById('updater_stop')

function startAndMonitorThreads(){
    const listener = new EventSource('http://127.0.0.1:5000/start_power_threads')

    listener.onopen = (e)=>{
        on_btn.style.display = 'none'
        
        off_btn.style.display = 'block'
        console.log('starting!')
    }

    let thread_counter = document.getElementById('thread_count')
    let status = document.getElementById('thread_status')

    listener.addEventListener('thread_count',(e)=>{
        console.log(e.data)
        thread_counter.innerHTML = e.data
        if (Number(e.data) >0){
            status.innerHTML = 'Online'

        } else {
            status.innerHTML = 'Offline'
        }
    })

    off_btn.addEventListener('click',()=>{
        listener.close()
        console.log('closing sse')
        on_btn.style.display = 'block'
        off_btn.style.display = 'none'
        thread_counter.innerHTML = 0
        status.innerHTML = 'Offline'
    })
}

const pwrModal = document.getElementById('power_config')

on_btn.addEventListener('click',()=>{
    pwrModal.showModal()
})
pwrModal.addEventListener("click", e => {
    const dialogDimensions = pwrModal.getBoundingClientRect()
    if (
      e.clientX < dialogDimensions.left ||
      e.clientX > dialogDimensions.right ||
      e.clientY < dialogDimensions.top ||
      e.clientY > dialogDimensions.bottom
    ) {
        pwrModal.close()
    }
  })

let formSelector = document.getElementById('power_type')

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

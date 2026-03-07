// Sample: memory_leak.js
// Issues: event listener leak, missing cleanup, var instead of const/let,
//         no error handling on fetch, callback hell

var activeListeners = []

function attachTracker(element, userId) {
  var handler = function(e) {
    logClick(userId, e.target)
  }
  // listener added but never removed — memory leak if element is re-rendered
  element.addEventListener('click', handler)
  activeListeners.push(handler)
}

function logClick(userId, target) {
  fetch('/api/log', {
    method: 'POST',
    body: JSON.stringify({ userId: userId, element: target.id })
    // missing headers, no .catch(), response not checked
  }).then(function(res) {
    res.json().then(function(data) {
      processLog(data, function(result) {
        saveResult(result, function(saved) {
          // callback hell — deeply nested, hard to follow
          console.log('saved', saved)
        })
      })
    })
  })
}

function initPage() {
  var buttons = document.querySelectorAll('button')
  for (var i = 0; i < buttons.length; i++) {
    // var in loop — i is shared across iterations (classic bug)
    attachTracker(buttons[i], i)
  }
}

initPage()

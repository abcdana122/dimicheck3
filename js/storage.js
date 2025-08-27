async function saveState(grade, section) {
  const magnets = {};
  document.querySelectorAll('.magnet:not(.placeholder)').forEach(m => {
    const num = m.dataset.number;
    const data = {};
    if (m.dataset.reason) data.reason = m.dataset.reason;
    if (m.classList.contains('attached')) {
      const sec = m.closest('.board-section');
      data.attachedTo = sec ? sec.dataset.category : null;
    } else {
      data.attachedTo = null;
      data.left = parseFloat(m.style.left) || 0;
      data.top  = parseFloat(m.style.top)  || 0;
    }
    magnets[num] = data;
  });

  try {
    await fetch(`/api/classes/state/save?grade=${grade}&section=${section}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ magnets })
    });
  } catch (e) {
    console.warn("saveState failed:", e);
  }
}

async function fetchMagnetConfig(grade, section) {
  try {
    const res = await fetch(`/api/classes/config?grade=${grade}&section=${section}`);
    if (!res.ok) throw new Error("config load failed");
    return await res.json();  // { end: 31, skipNumbers: [12, 20, 25] }
  } catch (e) {
    console.error("fetchMagnetConfig failed:", e);
    return { end: 30, skipNumbers: [] }; // 기본값 fallback
  }
}

function restoreToFreePosition(el, data) {
  const container = document.getElementById('magnetContainer');
  if (!container) return;

  // 섹션에서 떼어내고 컨테이너로 복귀
  el.classList.remove('attached');
  container.appendChild(el);

  // 자유 상태에서는 이유 제거
  if (el.dataset.reason) {
    delete el.dataset.reason;
    el.classList.remove('has-reason');
  }

  // 저장된 좌표가 있으면 사용, 없으면 그리드 기본 자리로
  const L = Number(data && data.left);
  const T = Number(data && data.top);
  if (!Number.isNaN(L) && !Number.isNaN(T)) {
    el.style.left = `${L}px`;
    el.style.top  = `${T}px`;
    el.style.transform = 'translate(0,0)';
  } else {
    // 기본 고정격자 좌표로 스냅
    snapToHome(el);
  }
}

async function loadState(grade, section) {
  try {
    const res = await fetch(`/api/classes/state/load?grade=${grade}&section=${section}`);
    if (!res.ok) throw new Error("로드 실패");
    const parsed = await res.json();
    const magnets = parsed.magnets || {};

    console.log(magnets);
    let didNormalizeSection = false;

    // 자석 반영
    Object.entries(magnets).forEach(([num, data]) => {
      const el = document.querySelector(`.magnet[data-number="${num}"]`);
      if (!el) return;

      //console.log(data.attachedTo);
      if (data.attachedTo == "section"){
        console.log('dd');
        restoreToFreePosition(el, data);
        didNormalizeSection = true;
        return; // 완료했으니 다음으로
      }

      if (data.attachedTo) {
        const sec = document.querySelector(`.board-section[data-category="${data.attachedTo}"] .section-content`);
        if (sec) {
          el.classList.add("attached");
          if (data.reason) {
            el.dataset.reason = data.reason.trim();   // ✅ reason 저장
            el.classList.add("has-reason");
          } else {
            delete el.dataset.reason;                 // ✅ reason 없을 때는 삭제
            el.classList.remove("has-reason");
          }
          sec.appendChild(el);
          return;
        }

        restoreToFreePosition(el, data);
        return;
      }

      restoreToFreePosition(el, data);
    });

    // ✅ 끝나고 기타 패널 갱신
    updateEtcReasonPanel();
    sortAllSections();
    updateAttendance();
    updateMagnetOutline();

    if (didNormalizeSection){
      await saveState(grade, section);
    }

  } catch (e) {
    console.error("loadState error:", e);
  }
}

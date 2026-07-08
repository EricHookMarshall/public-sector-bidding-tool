// Shared layout for the not-yet-built stages: a labelled preview screen on the
// left, the scope card on the right. The data inside each screen is realistic
// but illustrative — these stages aren't built, so the banner says so plainly
// (this project exists because a real admin failure was hidden; we don't dress
// mock-ups up as working software).
import ScopeCard from "./ScopeCard.jsx";

export function MockStage({ stage, addr, children }) {
  return (
    <div className="split">
      <div>
        <div className="preview-note">
          ● Preview — illustrative data. This stage is designed, not built yet.
        </div>
        <Screen addr={addr}>{children}</Screen>
      </div>
      <ScopeCard stage={stage} />
    </div>
  );
}

// Browser-window chrome around a mock screen.
export function Screen({ addr, children }) {
  return (
    <div className="screen">
      <div className="screen-bar">
        <div className="dots"><i /><i /><i /></div>
        <div className="addr">{addr}</div>
      </div>
      <div className="screen-body">{children}</div>
    </div>
  );
}

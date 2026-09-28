// A photo printed the way a two-colour risograph prints it: a soft colour
// underprint of the photo itself, and a navy key plate screened into halftone
// dots on top. The key is made in CSS: the photo, greyed and softened, sits
// under a 45-degree dot screen at half strength, and a steep contrast filter
// thresholds the sum, so each dot grows with the darkness beneath it as a real
// halftone does. The ink layer turns the black dots to the press ink, and the
// key multiplies onto the underprint the way ink overprints ink. See .riso in
// main.css; an entry being hovered develops toward the original photo.
//
// The project images are illustrative placeholders, not documentation, so the
// print is decorative: hidden from assistive technology, lazily loaded (both
// layers share one request) unless it sits above the fold (`eager`).
const RisoPrint = ({ src, className = '', eager = false }) => {
  const loading = eager ? 'eager' : 'lazy'
  return (
    <div className={`riso${src ? '' : ' riso-blank'}${className ? ` ${className}` : ''}`} aria-hidden="true">
      {src && (
        <div className="riso-under">
          <img src={src} alt="" loading={loading} decoding="async" />
        </div>
      )}
      <div className="riso-key">
        <div className="riso-plate">
          {src && <img src={src} alt="" loading={loading} decoding="async" />}
          <span className="riso-screen" />
        </div>
      </div>
    </div>
  )
}

export default RisoPrint

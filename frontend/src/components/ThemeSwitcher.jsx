import { HiColorSwatch, HiMoon, HiSun, HiChip } from 'react-icons/hi'
import { FaTree } from 'react-icons/fa'

const themes = [
    { id: 'default', name: 'Deep Space', icon: <HiMoon /> },
    { id: 'cyber', name: 'Cyber Neon', icon: <HiChip /> },
    { id: 'light', name: 'Minimal Light', icon: <HiSun /> },
    { id: 'forest', name: 'Forest Dark', icon: <FaTree /> }
]

export default function ThemeSwitcher({ currentTheme, onThemeChange }) {
    const currentIndex = themes.findIndex(t => t.id === currentTheme)
    const currentThemeData = themes[currentIndex] || themes[0]

    const handleCycle = (e) => {
        const nextIndex = (currentIndex + 1) % themes.length
        onThemeChange(themes[nextIndex].id)
    }

    return (
        <div className="theme-switcher" title={`Tema actual: ${currentThemeData.name}`}>
            <button
                className="theme-switcher__trigger"
                onClick={handleCycle}
            >
                {currentThemeData.icon}
            </button>
            <div className="theme-switcher__dropdown">
                {themes.map(theme => (
                    <button
                        key={theme.id}
                        className={`theme-icon-btn ${currentTheme === theme.id ? 'theme-icon-btn--active' : ''}`}
                        onClick={() => onThemeChange(theme.id)}
                        title={theme.name}
                    >
                        {theme.icon}
                    </button>
                ))}
            </div>
        </div>
    )
}

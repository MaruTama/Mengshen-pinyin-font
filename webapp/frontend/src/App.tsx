import { Navigate, Route, Routes } from 'react-router-dom'
import Home from './pages/Home'
import ProjectLayout from './pages/ProjectLayout'
import FontsStep from './pages/FontsStep'
import LicenseStep from './pages/LicenseStep'
import AdjustStep from './pages/AdjustStep'
import GlyphsStep from './pages/GlyphsStep'
import DuoyinziStep from './pages/DuoyinziStep'
import ReadingsStep from './pages/ReadingsStep'
import BuildStep from './pages/BuildStep'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/projects/:projectId" element={<ProjectLayout />}>
        <Route index element={<Navigate to="fonts" replace />} />
        <Route path="fonts" element={<FontsStep />} />
        <Route path="license" element={<LicenseStep />} />
        <Route path="adjust" element={<AdjustStep />} />
        <Route path="glyphs" element={<GlyphsStep />} />
        <Route path="readings" element={<ReadingsStep />} />
        <Route path="duoyinzi" element={<DuoyinziStep />} />
        <Route path="build" element={<BuildStep />} />
      </Route>
    </Routes>
  )
}

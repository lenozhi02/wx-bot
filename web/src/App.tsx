import { Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { MissionControl } from './pages/MissionControl';
import { SystemCharts } from './pages/SystemCharts';
import { PluginHub } from './pages/PluginHub';

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/tasks" element={<MissionControl />} />
        <Route path="/charts" element={<SystemCharts />} />
        <Route path="/plugins" element={<PluginHub />} />
      </Routes>
    </Layout>
  );
}

export default App;

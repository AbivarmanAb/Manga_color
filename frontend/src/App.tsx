import React, { useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { Dashboard } from './pages/Dashboard';
import { NewProjectWizard } from './pages/NewProjectWizard';
import { ProjectsList } from './pages/ProjectsList';
import { ColorizationStudio } from './pages/ColorizationStudio';
import { CharacterLibrary } from './pages/CharacterLibrary';
import { ReferenceManager } from './pages/ReferenceManager';
import { ProcessingQueuePage } from './pages/ProcessingQueuePage';
import { ExportCenter } from './pages/ExportCenter';
import { SettingsPage } from './pages/SettingsPage';
import { useStudioStore } from './stores/useStudioStore';
import { api } from './services/api';

export const App: React.FC = () => {
  const { currentTab, refreshHardware, refreshQueue, activeProjectId, setActiveProject } = useStudioStore();

  useEffect(() => {
    refreshHardware();
    refreshQueue();

    // Auto-select most recent project if none active
    api.getProjects().then((projs) => {
      if (projs.length > 0 && !activeProjectId) {
        setActiveProject(projs[0].id);
      }
    }).catch(console.error);

    const interval = setInterval(() => {
      refreshHardware();
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-studio-950 text-zinc-100 font-sans">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto">
          {currentTab === 'dashboard' && <Dashboard />}
          {currentTab === 'new-project' && <NewProjectWizard />}
          {currentTab === 'projects' && <ProjectsList />}
          {currentTab === 'studio' && <ColorizationStudio />}
          {currentTab === 'characters' && <CharacterLibrary />}
          {currentTab === 'references' && <ReferenceManager />}
          {currentTab === 'queue' && <ProcessingQueuePage />}
          {currentTab === 'exports' && <ExportCenter />}
          {currentTab === 'settings' && <SettingsPage />}
        </main>
      </div>
    </div>
  );
};

export default App;

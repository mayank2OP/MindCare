import ChatWidget from '../components/ChatWidget';

export default function Chat() {
  return (
    <div className="max-w-3xl mx-auto p-4 flex flex-col" style={{ height: 'calc(100vh - 56px)' }}>
      <ChatWidget />
    </div>
  );
}

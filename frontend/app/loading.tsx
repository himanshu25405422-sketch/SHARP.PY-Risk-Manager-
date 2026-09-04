export default function Loading() {
  return (
    <main className="min-h-screen bg-[#f4f3ef]">

      <div className="flex min-h-screen">

        <aside className="hidden w-60 bg-[#eeede8] p-6 lg:block">

          <div className="h-10 w-36 animate-pulse bg-neutral-200" />

          <div className="mt-12 space-y-3">

            <div className="h-10 animate-pulse bg-white" />
            <div className="h-10 animate-pulse bg-neutral-200" />
            <div className="h-10 animate-pulse bg-neutral-200" />

          </div>

        </aside>


        <section className="flex-1 p-8">

          <div className="h-8 w-52 animate-pulse bg-neutral-200" />

          <div className="mt-8 grid gap-px bg-[#deddd7] sm:grid-cols-2 xl:grid-cols-4">

            <div className="h-32 animate-pulse bg-white" />
            <div className="h-32 animate-pulse bg-white" />
            <div className="h-32 animate-pulse bg-white" />
            <div className="h-32 animate-pulse bg-white" />

          </div>


          <div className="mt-8 h-[500px] animate-pulse bg-white" />

        </section>

      </div>

    </main>
  );
}
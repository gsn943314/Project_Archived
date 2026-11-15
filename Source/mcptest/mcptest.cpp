#include "mcptest.h"
#include "Modules/ModuleManager.h"
#include "Misc/CoreDelegates.h"
#include "HAL/IConsoleManager.h"
#include "RenderUtils.h"
#include "RHIGlobals.h"

/**
 * Game module. Only job besides existing: on the web (Wasm) mobile *forward* tier, turn post-process materials
 * off. The gouache passes read GBuffer scene textures (DiffuseColor, WorldNormal) that the forward tier does not
 * have, so they fail to compile for SF_WEBGPU_ES3_1 and the engine would draw the default material over the whole
 * screen. The mobile deferred tier (desktop-class GPUs) and every other platform keep their post-process materials.
 */
class FMcptestGameModule : public FDefaultGameModuleImpl
{
public:
	virtual void StartupModule() override
	{
#if defined(PLATFORM_WASM) && PLATFORM_WASM
		FCoreDelegates::OnPostEngineInit.AddLambda([]()
		{
			const EShaderPlatform Platform = GMaxRHIShaderPlatform;
			if (IsMobilePlatform(Platform) && !IsMobileDeferredShadingEnabled(Platform))
			{
				if (IConsoleVariable* CVar = IConsoleManager::Get().FindConsoleVariable(TEXT("r.PostProcessing.DisableMaterials")))
				{
					CVar->Set(1, ECVF_SetByGameSetting);
					UE_LOG(LogTemp, Display, TEXT("mcptest: web forward tier, post-process materials off (gouache needs the deferred tier)"));
				}
			}
		});
#endif
	}
};

IMPLEMENT_PRIMARY_GAME_MODULE(FMcptestGameModule, mcptest, "mcptest");

from typing import List
from pathlib import Path
from discord.ext import commands
from src.utils.logging import logger


class FeatureManager:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.features_path = Path("src/features")
        self.loaded_features: List[str] = []
        self.disabled_features: List[str] = []

    async def load_all_features(self) -> None:
        """Load all feature modules from the features directory"""
        if not self.features_path.exists():
            logger.info("Creating features directory...")
            self.features_path.mkdir(parents=True, exist_ok=True)
            return

        for feature_dir in self.features_path.iterdir():
            if feature_dir.is_dir() and not feature_dir.name.startswith("_"):
                await self.load_feature(feature_dir.name)

    async def load_feature(self, feature_name: str) -> bool:
        """Load a specific feature by name"""
        if feature_name in self.disabled_features:
            logger.warning(f"Feature '{feature_name}' is disabled")
            return False

        try:
            # Check for cog.py or main.py in feature directory
            feature_path = self.features_path / feature_name
            cog_file = next(
                (f for f in ["cog.py", "main.py"] if (feature_path / f).exists()), None
            )

            if not cog_file:
                logger.error(f"No cog.py or main.py found in feature '{feature_name}'")
                return False

            # Load the extension
            module_path = f"src.features.{feature_name}.{cog_file[:-3]}"
            await self.bot.load_extension(module_path)

            self.loaded_features.append(feature_name)
            logger.info(f"Loaded feature: {feature_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to load feature '{feature_name}': {str(e)}")
            return False

    async def unload_feature(self, feature_name: str) -> bool:
        """Unload a specific feature by name"""
        try:
            # Try both possible module paths
            for module_suffix in ["cog", "main"]:
                try:
                    module_path = f"src.features.{feature_name}.{module_suffix}"
                    await self.bot.unload_extension(module_path)
                    self.loaded_features.remove(feature_name)
                    logger.info(f"Unloaded feature: {feature_name}")
                    return True
                except commands.ExtensionNotFound:
                    continue

            logger.error(f"Feature '{feature_name}' not found")
            return False

        except Exception as e:
            logger.error(f"Failed to unload feature '{feature_name}': {str(e)}")
            return False

    async def reload_feature(self, feature_name: str) -> bool:
        """Reload a specific feature by name"""
        await self.unload_feature(feature_name)
        return await self.load_feature(feature_name)

    def disable_feature(self, feature_name: str) -> None:
        """Disable a feature from being loaded"""
        if feature_name not in self.disabled_features:
            self.disabled_features.append(feature_name)

    def enable_feature(self, feature_name: str) -> None:
        """Enable a previously disabled feature"""
        if feature_name in self.disabled_features:
            self.disabled_features.remove(feature_name)

    @property
    def available_features(self) -> List[str]:
        """Get a list of all available features"""
        return [
            d.name
            for d in self.features_path.iterdir()
            if d.is_dir() and not d.name.startswith("_")
        ]

    async def unload_all_features(self) -> None:
        """Unload all currently loaded features"""
        for feature_name in (
            self.loaded_features.copy()
        ):  # Use copy to avoid modifying list during iteration
            try:
                await self.unload_feature(feature_name)
            except Exception as e:
                logger.error(f"Failed to unload feature '{feature_name}': {str(e)}")

"""
Dynamic model generator based on CONFIG_METADATA

Generates SQLModel classes dynamically from configuration metadata,
eliminating hardcoded model definitions.
"""
from typing import Dict, Any, Optional, Type, Tuple
from sqlmodel import SQLModel, Field
from pydantic import field_validator, create_model
from config.constants import CONFIG_METADATA, ConfigType


class SettingModelGenerator:
    """Dynamic model generator"""
    
    @staticmethod
    def _get_python_type(config_type: ConfigType, required: bool = True) -> Type:
        """Convert ConfigType to Python type"""
        type_mapping = {
            ConfigType.STRING: str,
            ConfigType.INTEGER: int,
            ConfigType.FLOAT: float,
            ConfigType.BOOLEAN: bool
        }
        
        base_type = type_mapping[config_type]
        return base_type if required else Optional[base_type]
    
    @staticmethod
    def _create_encrypted_property(field_name: str):
        """Create property method for encrypted fields"""
        from .crypto import crypto_manager
        
        encrypted_field_name = f"{field_name}_encrypted"
        
        def getter(self):
            encrypted_value = getattr(self, encrypted_field_name, None)
            if not encrypted_value:
                return "" if field_name.endswith('_key') else ""
            return crypto_manager.decrypt(encrypted_value)
        
        def setter(self, value: str):
            encrypted_value = crypto_manager.encrypt(value) if value else ""
            setattr(self, encrypted_field_name, encrypted_value)
        
        return property(getter, setter)
    
    @classmethod
    def _generate_filed(
        cls,
        key: str,
        metadata: Dict[str, Any],
        is_optional: bool = False
        ) -> Tuple[Type, Field]:
        metadata = CONFIG_METADATA[key]
        
        field_type = None
        field_properties : Dict[str, Any]  = {}
        if metadata.get('sensitive', False):
            field_type = cls._get_python_type(ConfigType.STRING, metadata.get('required', False))
            if not metadata.get('required', False):
                field_properties['default'] = None
        else:
            field_type = cls._get_python_type(metadata['type'], metadata.get('required', False))
            if 'default' in metadata:
                field_properties['default'] = metadata['default']
            elif not metadata.get('required', False):
                field_properties['default'] = None
                
        if metadata.get('nullable', False):
            field_properties['nullable'] = True
        
        # Handle validation, validation rules are defined in metadata
        if metadata.get('validation'):
            for key, value in metadata['validation'].items():
                field_properties[key] = value

        # If optional field, set default value to None and make it nullable
        if is_optional:
            field_properties['default'] = None
            field_properties['nullable'] = True
        
        if field_properties:
            return field_type, Field(**field_properties)
        else:
            return field_type, Field()
            
            
    
    @classmethod
    def create_setting_model(cls) -> Type[SQLModel]:
        """Dynamically create Setting model"""
        from .crypto import crypto_manager

        # Prepare field definitions
        fields = {}

        # Add id field
        fields['id'] = (Optional[int], Field(default=None, primary_key=True))

        # Handle configuration fields
        for key, metadata in CONFIG_METADATA.items():
            field_key = key if not metadata.get('sensitive', False) else f"{key}_encrypted"
            field_type, field = cls._generate_filed(key, metadata)
            fields[field_key] = (field_type, field)

        # Use create_model to create base model
        Setting = create_model(
            'Setting',
            __base__=SQLModel,
            __cls_kwargs__={"table": True},
            **fields
        )


        # Add properties for sensitive fields
        for key, metadata in CONFIG_METADATA.items():
            if metadata.get('sensitive', False):
                prop = cls._create_encrypted_property(key)
                setattr(Setting, key, prop)

        return Setting

    @classmethod
    def create_setting_response_model(cls) -> Type[SQLModel]:
        """Dynamically create SettingResponse model"""
        # Use create_model to create response model
        fields = {'id': (int, ...)}

        for key, metadata in CONFIG_METADATA.items():
            # Response models use original key names (sensitive fields are accessed through properties for decryption)
            field_type = cls._get_python_type(metadata['type'], required=False)
            default_value = metadata.get('default')

            if default_value is not None:
                fields[key] = (field_type, default_value)
            else:
                fields[key] = (field_type, None)

        return create_model(
            'SettingResponse',
            __base__=SQLModel,
            **fields
        )

    @classmethod
    def create_setting_update_model(cls) -> Type[SQLModel]:
        """Dynamically create SettingUpdate model"""
        fields = {}

        for key, metadata in CONFIG_METADATA.items():
            # All fields in update model are optional
            field_type, field = cls._generate_filed(key, metadata, is_optional=True)
            fields[key] = (field_type, field)

        # Create model
        SettingUpdate = create_model(
            'SettingUpdate',
            __base__=SQLModel,
            **fields
        )

        return SettingUpdate


# Generate model instances
Setting = SettingModelGenerator.create_setting_model()
SettingResponse = SettingModelGenerator.create_setting_response_model()
SettingUpdate = SettingModelGenerator.create_setting_update_model()
